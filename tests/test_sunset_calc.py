import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sunset_time_calc import SunsetCalculator

from datetime import datetime, timedelta, timezone

# Example usage
if __name__ == "__main__":
    calculator = SunsetCalculator()

    # Test locations
    test_locations = [
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    ]

    # Calculate sunset for today
    today = datetime.now().date()
    print(f"Sunset times for {today.strftime('%Y-%m-%d')}:")

    for location in test_locations:
        sunset = calculator.calculate_sunset(location["lat"], location["lon"])
        print(f"{location['name']}: {sunset.strftime('%H:%M:%S')}")

    # Generate a grid for the San Francisco Bay Area
    print("\nGenerating sunset grid for SF Bay Area...")
    sf_grid = calculator.get_grid_sunset_times(
        37.0, -123.0, 38.0, -121.0, grid_size=0.1
    )
    print(f"Generated grid with {len(sf_grid)} points")

    # Test with a specific position using the grid
    test_lat, test_lon = 37.65, -122.07
    sunset_from_grid = calculator.get_sunset_for_position(
        test_lat, test_lon, grid=sf_grid
    )
    sunset_direct = calculator.calculate_sunset(test_lat, test_lon)

    print(f"\nTest position ({test_lat}, {test_lon}):")
    print(f"Sunset from grid: {sunset_from_grid.strftime('%H:%M:%S')}")
    print(f"Sunset direct calculation: {sunset_direct.strftime('%H:%M:%S')}")
    print(
        f"Difference: {abs((sunset_from_grid - sunset_direct).total_seconds() / 60):.2f} minutes"
    )
