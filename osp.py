import time
import json
import uuid
import hashlib
from datetime import datetime, timezone


class PulseGenerator:
    """
    Generate one-second pulses with sunset-specific sequences
    """

    def __init__(self, cascade_length=6000):
        """
        Initialize the pulse generator

        Args:
            cascade_length: Length of the sunset cascade sequence in seconds
        """
        self.cascade_length = cascade_length
        self.sequence_cache = {}  # Cache for generated sequences

    def generate_sunset_sequence(self, latitude, longitude, sunset_time):
        """
        Generate a unique sequence based on location and sunset time

        Args:
            latitude: Latitude of the position
            longitude: Longitude of the position
            sunset_time: Datetime object representing the sunset time

        Returns:
            A byte sequence derived from the inputs
        """
        # Create a cache key for this location and date
        cache_key = f"{latitude:.4f}_{longitude:.4f}_{sunset_time.date().isoformat()}"

        # Check if we have this sequence cached
        if cache_key in self.sequence_cache:
            return self.sequence_cache[cache_key]

        # Generate a seed string from the inputs
        seed = f"{latitude:.6f}_{longitude:.6f}_{sunset_time.timestamp()}"

        # Create a hash of the seed
        hash_obj = hashlib.sha256(seed.encode())

        # Use the hash to seed a simple PRNG
        hash_bytes = hash_obj.digest()

        # Store in cache
        self.sequence_cache[cache_key] = hash_bytes

        return hash_bytes

    def compress_cascade(self, cascade_sequence):
        """
        Compress a cascade sequence into a one-second pulse

        Args:
            cascade_sequence: The full cascade sequence

        Returns:
            A compressed one-second pulse
        """
        # For simplicity, we'll just use a hash of the cascade sequence
        # In a real implementation, this would involve more sophisticated compression
        hasher = hashlib.sha256()
        hasher.update(cascade_sequence)
        return hasher.digest()

    def generate_pulse(self, latitude, longitude, sunset_time, current_time):
        """
        Generate a one-second pulse for a specific position and time

        Args:
            latitude: Latitude of the position
            longitude: Longitude of the position
            sunset_time: Datetime object representing the sunset time
            current_time: Current datetime object

        Returns:
            A dictionary containing the pulse data
        """
        # Generate the sunset-specific sequence
        sequence = self.generate_sunset_sequence(latitude, longitude, sunset_time)

        # In a real implementation, we would use the current_time to determine
        # where in the 6000-second cascade we are, but for this demo we'll
        # just use a simplified approach

        # Simulate position in the cascade (0 to cascade_length-1)
        seconds_since_sunset = max(0, int((current_time - sunset_time).total_seconds()))
        position = seconds_since_sunset % self.cascade_length

        # Extract a segment of the sequence based on position
        cascade_segment = (
            sequence[position % len(sequence) :] + sequence[: position % len(sequence)]
        )

        # Compress the cascade into a one-second pulse
        pulse = self.compress_cascade(cascade_segment)

        # Create a pulse data structure
        pulse_data = {
            "id": str(uuid.uuid4()),
            "timestamp": current_time.timestamp(),
            "latitude": latitude,
            "longitude": longitude,
            "sunset_time": sunset_time.timestamp(),
            "cascade_position": position,
            "pulse_hash": pulse.hex()[:16],  # Use first 16 chars of hex for readability
        }

        return pulse_data
