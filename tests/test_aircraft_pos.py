import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aircraft_pos import PositionInterpolator

if __name__ == "__main__":
    # Create an interpolator
    interpolator = PositionInterpolator()

    # Mock aircraft data
    aircraft1 = {
        "icao24": "abc123",
        "timestamp": time.time(),
        "latitude": 37.7749,
        "longitude": -122.4194,
        "altitude": 10000,
        "velocity": 200,  # 200 m/s = ~720 km/h
        "heading": 90,  # East
    }

    interpolator.update_aircraft_position(aircraft1)

    time.sleep(1)

    current_time = time.time()
    interpolated = interpolator.interpolate_position("abc123", current_time)

    print("Original Position:")
    print(f"  Latitude: {aircraft1['latitude']}")
    print(f"  Longitude: {aircraft1['longitude']}")

    print("\nInterpolated Position:")
    print(f"  Latitude: {interpolated['latitude']}")
    print(f"  Longitude: {interpolated['longitude']}")
    print(f"  Plus Code: {interpolated['plus_code']}")

    distance = aircraft1["velocity"] * (current_time - aircraft1["timestamp"])
    print(f"\nExpected distance traveled: {distance:.2f} meters")
