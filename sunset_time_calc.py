import math
import datetime
import time
import json
import os
from datetime import datetime, timedelta, timezone
from helisol import Sun

class SunsetCalculator:
    """Calculate sunset times for specific locations and dates"""

    def __init__(self, cache_file="sunset_cache.json"):
        """
        Initialize the sunset calculator

        Args:
            cache_file: File to store cached sunset times
        """
        if cache_file is None:
            import os
            cache_file = "/tmp/sunset_cache.json" if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else "sunset_cache.json"
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        """Load the cached sunset times from file if it exists"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Error loading cache file, creating new cache")
        return {}

    def _save_cache(self):
        """Save the cached sunset times to file"""
        if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
            return
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            print(f"Error saving cache file: {e}")

    def calculate_sunset(self, latitude, longitude, date=None):
        """
        Calculate sunset time for a given location and date

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date object (defaults to today)

        Returns:
            Datetime object representing the sunset time in local timezone
        """
        if date is None:
            date = datetime.now().date()

        cache_key = f"{latitude:.4f}_{longitude:.4f}_{date.isoformat()}"

        if cache_key in self.cache:
            sunset_timestamp = self.cache[cache_key]
            return datetime.fromtimestamp(sunset_timestamp)

        day_of_year = date.timetuple().tm_yday

        lat_rad = math.radians(latitude)
        lng_rad = math.radians(longitude)

        sun = Sun()
        declination = sun.declination

        # Calculate the sunset hour angle
        hour_angle = math.acos(-math.tan(lat_rad) * math.tan(declination))

        # Convert to hours, with noon = 0
        sunset_hour = 12 + (hour_angle * 12 / math.pi)

        # Adjust for longitude (every 15 degrees = 1 hour)
        timezone_offset = round(longitude / 15)
        local_sunset_hour = sunset_hour - longitude / 15 + timezone_offset

        sunset_minutes = (local_sunset_hour - int(local_sunset_hour)) * 60
        sunset_time = datetime.combine(
            date,
            datetime.min.time().replace(
                hour=int(local_sunset_hour) % 24, minute=int(sunset_minutes)
            ),
        )

        # Cache the result
        self.cache[cache_key] = sunset_time.timestamp()
        self._save_cache()

        return sunset_time

    def get_grid_sunset_times(
        self, min_lat, min_lon, max_lat, max_lon, grid_size=0.1, date=None
    ):
        """
        Generate a grid of sunset times for a region

        Args:
            min_lat: Minimum latitude
            min_lon: Minimum longitude
            max_lat: Maximum latitude
            max_lon: Maximum longitude
            grid_size: Grid cell size in degrees
            date: Date object (defaults to today)

        Returns:
            Dictionary mapping grid cells to sunset times
        """
        if date is None:
            date = datetime.now().date()

        sunset_grid = {}

        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                sunset = self.calculate_sunset(lat, lon, date)

                # Store in grid
                grid_key = f"{lat:.4f}_{lon:.4f}"
                sunset_grid[grid_key] = sunset.timestamp()

                lon += grid_size
            lat += grid_size

        return sunset_grid

    def get_sunset_for_position(
        self, latitude, longitude, date=None, grid=None, grid_size=0.1
    ):
        """
        Get sunset time for a specific position

        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            date: Date object (defaults to today)
            grid: Optional pre-computed grid of sunset times
            grid_size: Grid cell size if using the grid

        Returns:
            Datetime object representing the sunset time
        """
        if grid:
            lat_grid = round(latitude / grid_size) * grid_size
            lon_grid = round(longitude / grid_size) * grid_size
            grid_key = f"{lat_grid:.4f}_{lon_grid:.4f}"

            if grid_key in grid:
                return datetime.fromtimestamp(grid[grid_key])

        # If no grid or point not found, calculate directly
        return self.calculate_sunset(latitude, longitude, date)
