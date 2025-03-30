import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime
from sunset_time_calc import SunsetCalculator
from lattice_clock import LatticeClockSystem

def sunset_tick_callback(timestamp, calculator, clock):
    """
    Callback function for the lattice clock that tests sunset calculations

    Args:
        timestamp: Current datetime from the lattice clock
        calculator: SunsetCalculator instance
        clock: LatticeClockSystem instance
    """
    print(f"\n--- TICK: {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC ---")

    # Test locations
    test_locations = [
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    ]

    for location in test_locations:
        # Check if it's after sunset at this location
        is_after_sunset = clock.is_after_sunset(location["lat"], location["lon"])

        # Get the sunset time for this location
        sunset_time = calculator.calculate_sunset(location["lat"], location["lon"])

        # Format the status message
        status = "after sunset" if is_after_sunset else "before sunset"

        print(
            f"  {location['name']}: {status} (sunset at {sunset_time.strftime('%H:%M:%S')})"
        )


def main():
    print("Testing Sunset Calculator with Lattice Clock...")

    # Create the sunset calculator
    calculator = SunsetCalculator()

    # Create the lattice clock
    lattice = LatticeClockSystem()

    # Generate a sunset grid for the San Francisco Bay Area
    print("\nGenerating sunset grid for SF Bay Area...")
    sf_grid = calculator.get_grid_sunset_times(
        37.0, -123.0, 38.0, -121.0, grid_size=0.5
    )
    lattice.add_sunset_grid("SF_Bay_Area", sf_grid)

    # Generate a sunset grid for the New York area
    print("Generating sunset grid for New York area...")
    ny_grid = calculator.get_grid_sunset_times(40.0, -75.0, 41.0, -73.0, grid_size=0.5)
    lattice.add_sunset_grid("NY_Area", ny_grid)

    # Register our tick callback
    lattice.register_callback(
        lambda timestamp: sunset_tick_callback(timestamp, calculator, lattice)
    )

    # Start the lattice clock
    print("\nStarting lattice clock...")
    lattice.start()

    # Run for a short demo period
    try:
        num_ticks = 5
        print(f"\nRunning for {num_ticks} ticks...")
        time.sleep(num_ticks + 1)  # Add 1 to ensure we get all ticks
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Stop the lattice clock
        lattice.stop()

    print("\nTest completed!")


if __name__ == "__main__":
    main()
