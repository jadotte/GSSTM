import json
import time
from datetime import datetime
from plus_code_calculator import encode
from opensky_api import OpenSkyApi  # Import the official OpenSky API client


class FlightDataFetcher:
    """Class to fetch and process flight data from OpenSky Network API"""

    def __init__(self, username=None, password=None):
        """
        Initialize the fetcher with optional credentials

        Args:
            username: Optional OpenSky Network username
            password: Optional OpenSky Network password
        """
        # Initialize the official OpenSky API client
        self.api = OpenSkyApi(username, password)

    def fetch_current_states(self, bbox=None, retry_attempts=3, retry_delay=15):
        """
        Fetch current aircraft states from OpenSky Network

        Args:
            bbox: Optional bounding box as [min_lat, min_lon, max_lat, max_lon]
                 to restrict the results to a specific area
            retry_attempts: Number of retry attempts if API fails
            retry_delay: Delay between retries in seconds

        Returns:
            A list of aircraft data with Plus Codes added
        """
        for attempt in range(retry_attempts):
            try:
                # Wait between retries (but not on first attempt)
                if attempt > 0:
                    print(
                        f"Retry attempt {attempt + 1}/{retry_attempts}, waiting {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)

                print(
                    f"Fetching flight data (attempt {attempt + 1}/{retry_attempts})..."
                )

                if bbox:
                    min_lat, min_lon, max_lat, max_lon = bbox
                    print(
                        f"Using bounding box: min_lat={min_lat}, max_lat={max_lat}, min_lon={min_lon}, max_lon={max_lon}"
                    )
                    states = self.api.get_states(
                        bbox=(min_lat, max_lat, min_lon, max_lon)
                    )
                else:
                    print("Fetching global states (no bounding box)")
                    states = self.api.get_states()

                # Check if the API call was successful
                if states is None:
                    print(
                        "Error: API returned None - possible rate limiting or connection issue"
                    )
                    continue

                # Process the data and add Plus Codes
                if states and states.states:
                    processed_data = self._process_states(states)
                    return processed_data
                else:
                    print("No aircraft states found in the response")
                    continue

            except Exception as e:
                print(f"Error fetching flight data: {e}")

        # If we get here, all retries failed
        print("All API attempts failed. Returning empty result.")
        return []

    def _process_states(self, states_obj):
        """
        Process the states object from OpenSky API

        Args:
            states_obj: OpenSkyStates object from the API

        Returns:
            A list of processed aircraft data with Plus Codes
        """
        processed_aircraft = []

        if not states_obj or not states_obj.states:
            return processed_aircraft

        timestamp = states_obj.time

        for state in states_obj.states:
            # Skip aircraft without position data
            if state.longitude is None or state.latitude is None:
                continue

            plus_code = encode(state.latitude, state.longitude)

            # Note: Changed from 'heading' to 'true_track' to match OpenSky API
            aircraft = {
                "icao24": state.icao24,
                "callsign": state.callsign.strip() if state.callsign else None,
                "timestamp": timestamp,
                "position_time": state.time_position,
                "last_contact": state.last_contact,
                "longitude": state.longitude,
                "latitude": state.latitude,
                "altitude": state.baro_altitude,  # Barometric altitude in meters
                "on_ground": state.on_ground,
                "velocity": state.velocity,  # meters/sec
                "heading": state.true_track,  # Using true_track instead of heading
                "vertical_rate": state.vertical_rate,  # meters/sec
                "squawk": state.squawk,  # transponder code
                "origin_country": state.origin_country,
                "plus_code": plus_code,
            }

            processed_aircraft.append(aircraft)

        return processed_aircraft

    def save_to_file(self, data, filename="flight_data.json"):
        """
        Save processed flight data to a JSON file

        Args:
            data: Processed flight data
            filename: Output filename
        """
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} aircraft records to {filename}")


