import time
import datetime
import threading
import ntplib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Any


class LatticeClockSystem:
    """
    Lattice Clock System that references accurate time sources and incorporates
    regional sunset times for precise one-second pulses.
    """

    def __init__(self, ntp_server="pool.ntp.org"):
        """
        Initialize the Lattice Clock System

        Args:
            ntp_server: NTP server to use for time synchronization
        """
        self.ntp_server = ntp_server
        self.ntp_client = ntplib.NTPClient()
        self.system_offset = 0.0  # Offset between system time and NTP time
        self.sunset_grids: Dict[str, Dict[str, float]] = {}  # Region -> grid mapping
        self.callbacks: List[Callable] = []  # Callbacks to run on each tick
        self.running = False
        self.clock_thread = None
        self.last_sync = 0
        self.sync_interval = 3600  # Sync with NTP every hour

        self._sync_time()

    def _sync_time(self):
        """Synchronize with NTP server to calculate system time offset"""
        try:
            response = self.ntp_client.request(self.ntp_server, version=3)
            # Calculate the offset between system time and NTP time
            self.system_offset = response.offset
            self.last_sync = time.time()
            print(
                f"Synchronized with NTP server. Offset: {self.system_offset:.6f} seconds"
            )
        except Exception as e:
            print(f"NTP synchronization failed: {e}")

    def get_accurate_time(self):
        """
        Get the current time, adjusted by the NTP offset

        Returns:
            Current datetime object with NTP correction applied
        """
        # Re-sync if necessary
        if time.time() - self.last_sync > self.sync_interval:
            self._sync_time()

        # Apply the offset
        accurate_timestamp = time.time() + self.system_offset
        return datetime.fromtimestamp(accurate_timestamp, tz=timezone.utc)

    def add_sunset_grid(self, region_name, sunset_grid):
        """
        Add a sunset grid for a specific region

        Args:
            region_name: Name of the region (e.g., "SF_Bay_Area")
            sunset_grid: Dictionary mapping grid points to sunset times
        """
        self.sunset_grids[region_name] = sunset_grid
        print(
            f"Added sunset grid for region '{region_name}' with {len(sunset_grid)} points"
        )

    def get_sunset_for_position(self, latitude, longitude, grid_size=0.1):
        """
        Get the sunset time for a specific position from loaded grids

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            grid_size: Grid cell size in degrees

        Returns:
            Datetime object representing the sunset time or None if not found
        """
        lat_grid = round(latitude / grid_size) * grid_size
        lon_grid = round(longitude / grid_size) * grid_size
        grid_key = f"{lat_grid:.4f}_{lon_grid:.4f}"

        # Check all regions for the grid point
        for region, grid in self.sunset_grids.items():
            if grid_key in grid:
                return datetime.fromtimestamp(grid[grid_key], tz=timezone.utc)

        return None

    def register_callback(self, callback: Callable):
        """
        Register a callback to be called on each clock tick

        Args:
            callback: Function to call, should accept a datetime object as argument
        """
        self.callbacks.append(callback)

    def _clock_loop(self):
        """Main clock loop that runs in a separate thread"""
        last_second = -1

        while self.running:
            now = self.get_accurate_time()
            current_second = now.second

            # If we've moved to a new second, trigger the callbacks
            if current_second != last_second:
                last_second = current_second

                # Call all registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(now)
                    except Exception as e:
                        print(f"Error in callback: {e}")

            # Sleep until close to the next second
            # Calculate milliseconds until next second
            next_second = timedelta(seconds=1) - timedelta(microseconds=now.microsecond)
            sleep_time = next_second.total_seconds() * 0.95  # Wake up slightly early
            time.sleep(sleep_time)

    def start(self):
        """Start the lattice clock"""
        if self.running:
            print("Lattice Clock is already running")
            return

        self.running = True
        self.clock_thread = threading.Thread(target=self._clock_loop, daemon=True)
        self.clock_thread.start()
        print("Lattice Clock started")

    def stop(self):
        """Stop the lattice clock"""
        if not self.running:
            print("Lattice Clock is not running")
            return

        self.running = False
        if self.clock_thread:
            self.clock_thread.join(timeout=2.0)
        print("Lattice Clock stopped")

    def is_after_sunset(self, latitude, longitude):
        """
        Check if the current time is after sunset at the given position

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees

        Returns:
            Boolean indicating if current time is after sunset
        """
        now = self.get_accurate_time()
        sunset = self.get_sunset_for_position(latitude, longitude)

        if not sunset:
            return None  # Unknown

        sunset = sunset.astimezone(now.tzinfo)
        return now > sunset


# Example usage and test harness
def demo_callback(timestamp):
    """Example callback function that prints the current time"""
    print(f"TICK: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

def flight_data_callback(timestamp, fetcher, calculator, lattice_clock):
    """
    Callback that processes flight data on each tick

    Args:
        timestamp: Current datetime from the lattice clock
        fetcher: FlightDataFetcher instance
        calculator: PulseGenerator instance (from osp.py)
        lattice_clock: LatticeClockSystem instance
    """
    print(f"Processing flight data at {timestamp.strftime('%H:%M:%S.%f')[:-3]}")

    try:
        # Using the fetch_current_states method from FlightDataFetcher
        aircraft_data = fetcher.fetch_current_states()
        
        if not aircraft_data:
            print("No aircraft data available")
            return
            
        print(f"Processing {len(aircraft_data)} aircraft")
        
        # Create a directory for storing flight data if it doesn't exist
        import os
        storage_dir = "flight_data"
        os.makedirs(storage_dir, exist_ok=True)
        
        date_str = timestamp.strftime("%Y-%m-%d")
        file_path = os.path.join(storage_dir, f"flight_records_{date_str}.jsonl")
        
        for aircraft in aircraft_data:
            try:
                callsign = aircraft.get("callsign", "UNKNOWN")
                latitude = aircraft.get("latitude")
                longitude = aircraft.get("longitude")
                altitude = aircraft.get("altitude", 0)
                if latitude is None or longitude is None:
                    print(f"  Skipping aircraft {callsign}: missing position data")
                    continue
                plus_code = aircraft.get("plus_code")
                sunset_time = lattice_clock.get_sunset_for_position(latitude, longitude)
                if sunset_time:
                    is_after_sunset = timestamp > sunset_time
                    sunset_status = "after sunset" if is_after_sunset else "before sunset"
                    if is_after_sunset:
                        pulse_data = calculator.generate_pulse(
                            latitude, longitude, sunset_time, timestamp
                        )
                    else:
                        pulse_data = None
                else:
                    sunset_status = "sunset time unknown"
                    pulse_data = None
                flight_record = {
                    "timestamp": timestamp.timestamp(),
                    "icao24": aircraft.get("icao24"),
                    "callsign": callsign,
                    "latitude": latitude,
                    "longitude": longitude,
                    "altitude": altitude,
                    "velocity": aircraft.get("velocity"),
                    "heading": aircraft.get("heading"),
                    "vertical_rate": aircraft.get("vertical_rate"),
                    "on_ground": aircraft.get("on_ground"),
                    "origin_country": aircraft.get("origin_country"),
                    "plus_code": plus_code,
                    "sunset_status": sunset_status,
                    "sunset_time": sunset_time.timestamp() if sunset_time else None,
                    "pulse_data": pulse_data
                }
                print(f"  Aircraft {callsign} at {latitude:.4f}, {longitude:.4f} ({plus_code}) is {sunset_status}")
                with open(file_path, "a") as f:
                    f.write(json.dumps(flight_record) + "\n")
                if pulse_data:
                    pulse_dir = os.path.join(storage_dir, "pulses")
                    os.makedirs(pulse_dir, exist_ok=True)
                    pulse_id = pulse_data["id"]
                    pulse_path = os.path.join(pulse_dir, f"{pulse_id}.json")
                    with open(pulse_path, "w") as f:
                        json.dump(pulse_data, f, indent=2)
                    print(f"    Generated pulse: {pulse_data['pulse_hash']} (cycle {pulse_data['cycle_number']})")
            except Exception as e:
                print(f"  Error processing aircraft {aircraft.get('callsign', 'UNKNOWN')}: {e}")
    
    except Exception as e:
        print(f"Error in flight data callback: {e}")
