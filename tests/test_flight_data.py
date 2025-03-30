import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flight_data_aq import FlightDataFetcher
if __name__ == "__main__":
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(
        description="Fetch flight data from OpenSky Network"
    )
    parser.add_argument("--username", "-u", help="OpenSky Network username")
    parser.add_argument("--password", "-p", help="OpenSky Network password")
    parser.add_argument(
        "--retries", "-r", type=int, default=3, help="Number of retry attempts"
    )
    parser.add_argument(
        "--delay", "-d", type=int, default=15, help="Seconds to wait between retries"
    )
    parser.add_argument(
        "--global",
        "-g",
        action="store_true",
        help="Fetch global data instead of SF area",
    )
    args = parser.parse_args()

    # Print information about anonymous vs. authenticated access
    if args.username and args.password:
        print(f"Using authenticated access with username: {args.username}")
    else:
        print("Warning: Using anonymous access (limited to 1 request per 10 seconds)")

    # Initialize the fetcher
    fetcher = FlightDataFetcher(username=args.username, password=args.password)

    # Define a bounding box for the San Francisco Bay Area
    sf_bbox = [37.0, -123.0, 38.0, -121.0]

    # Fetch current flight data
    if getattr(args, "global"):
        flight_data = fetcher.fetch_current_states(
            retry_attempts=args.retries, retry_delay=args.delay
        )
    else:
        flight_data = fetcher.fetch_current_states(
            bbox=sf_bbox, retry_attempts=args.retries, retry_delay=args.delay
        )

    # Display summary
    print(f"Retrieved data for {len(flight_data)} aircraft")

    if flight_data:
        # Print sample data for the first few aircraft
        for i, aircraft in enumerate(flight_data[:5]):
            print(f"\nAircraft {i + 1}:")
            print(f"  ICAO: {aircraft['icao24']}")
            print(f"  Callsign: {aircraft['callsign']}")
            print(f"  Position: ({aircraft['latitude']}, {aircraft['longitude']})")
            print(f"  Plus Code: {aircraft['plus_code']}")
            print(f"  Altitude: {aircraft['altitude']} meters")
            print(f"  Speed: {aircraft['velocity']} m/s")

        # Save all data to file
        fetcher.save_to_file(flight_data)
        print("\nScript completed successfully")
    else:
        print("\nNo aircraft data found. Possible reasons:")
        print("1. The OpenSky Network API might be experiencing issues")
        print("2. Your IP might be temporarily rate-limited")
        print("3. Try using authentication for more reliable access")
        print("4. Consider using the enhanced version with REST client fallback")
