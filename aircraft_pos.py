import math
import time
from datetime import datetime, timezone
from plus_code_calculator import encode
from haversine import inverse_haversine

class PositionInterpolator:
    """
    Interpolate aircraft positions against lattice clock ticks
    """

    def __init__(self):
        """Initialize the position interpolator"""
        self.previous_positions = {}

    def update_aircraft_position(self, aircraft_data):
        """
        Update the stored position for an aircraft

        Args:
            aircraft_data: Dictionary with aircraft position data
        """
        icao24 = aircraft_data.get("icao24")

        if not icao24:
            return

        # Store the position data
        self.previous_positions[icao24] = {
            "timestamp": aircraft_data.get("timestamp", time.time()),
            "latitude": aircraft_data.get("latitude"),
            "longitude": aircraft_data.get("longitude"),
            "altitude": aircraft_data.get("altitude"),
            "velocity": aircraft_data.get("velocity"),  # m/s
            "heading": aircraft_data.get("heading"),  # degrees
            "vertical_rate": aircraft_data.get("vertical_rate", 0),  # m/s
        }

    def interpolate_position(self, icao24, timestamp):
        """
        Interpolate the position of an aircraft at a specific time

        Args:
            icao24: ICAO24 identifier of the aircraft
            timestamp: Timestamp to interpolate position for

        Returns:
            Dictionary with interpolated position data or None if unavailable
        """
        if icao24 not in self.previous_positions:
            return None

        prev_data = self.previous_positions[icao24]

        if (
            prev_data.get("latitude") is None
            or prev_data.get("longitude") is None
            or prev_data.get("timestamp") is None
            or prev_data.get("velocity") is None
            or prev_data.get("heading") is None
        ):
            return None

        time_diff = timestamp - prev_data["timestamp"]

        # If the previous position is too old (> 15 seconds), don't interpolate
        if abs(time_diff) > 15:
            return None

        # Calculate distance traveled in meters
        distance = prev_data["velocity"] * time_diff

        heading_rad = math.radians()

        old_coord = (prev_data["latitude"], prev_data["longitude"])
        new_lat, new_lon = inverse_haversine(old_coord, distance * 1000, prev_data["heading"])
        new_alt = prev_data["altitude"]

        if prev_data.get("vertical_rate"):
            new_alt += prev_data["vertical_rate"] * time_diff

        plus_code = encode(new_lat, new_lon)

        return {
            "icao24": icao24,
            "timestamp": timestamp,
            "latitude": new_lat,
            "longitude": new_lon,
            "altitude": new_alt,
            "plus_code": plus_code,
            "interpolated": True,
        }

    def process_aircraft_data(self, aircraft_list, tick_timestamp):
        """
        Process a list of aircraft data against a lattice clock tick

        Args:
            aircraft_list: List of dictionaries with aircraft data
            tick_timestamp: Timestamp of the lattice clock tick

        Returns:
            List of processed aircraft data with interpolated positions
        """
        processed_data = []

        for aircraft in aircraft_list:
            self.update_aircraft_position(aircraft)

        for icao24 in self.previous_positions:
            current_data = next(
                (a for a in aircraft_list if a.get("icao24") == icao24), None
            )

            if current_data:
                processed_data.append(current_data)
            else:
                interpolated = self.interpolate_position(icao24, tick_timestamp)
                if interpolated:
                    processed_data.append(interpolated)

        return processed_data

    def cleanup_old_positions(self, max_age=60):
        """
        Remove stored positions that are older than max_age seconds

        Args:
            max_age: Maximum age of stored positions in seconds
        """
        current_time = time.time()
        to_remove = []

        for icao24, data in self.previous_positions.items():
            if current_time - data.get("timestamp", 0) > max_age:
                to_remove.append(icao24)

        for icao24 in to_remove:
            del self.previous_positions[icao24]

        if to_remove:
            print(f"Removed {len(to_remove)} old aircraft positions")
