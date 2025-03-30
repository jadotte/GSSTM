#!/usr/bin/env python3
"""
Test script for the pulse generator
"""

import time
import json
from datetime import datetime, timezone, timedelta
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osp import PulseGenerator

def main():
    print("Testing Pulse Generator...")
    
    # Create a pulse generator
    generator = PulseGenerator()
    
    # Test location (San Francisco)
    lat, lon = 37.7749, -122.4194
    
    # Mock sunset time (current time - 1 hour)
    current_time = datetime.now(timezone.utc)
    sunset_time = current_time.replace(hour=current_time.hour - 1)
    
    print(f"Current time: {current_time.isoformat()}")
    print(f"Sunset time: {sunset_time.isoformat()}")
    print(f"Test location: ({lat}, {lon})")
    
    # Generate a pulse
    pulse = generator.generate_pulse(lat, lon, sunset_time, current_time)
    
    # Print the pulse data
    print("\nGenerated Pulse:")
    print(json.dumps(pulse, indent=2))
    
    # Generate a series of pulses at 1-second intervals
    print("\nGenerating pulses at 1-second intervals:")
    
    for i in range(5):
        # Use timedelta to increment time
        tick_time = current_time + timedelta(seconds=i)
        
        # Generate pulse
        pulse = generator.generate_pulse(lat, lon, sunset_time, tick_time)
        
        # Print pulse hash
        print(f"  Pulse {i+1}: {pulse['pulse_hash']} (cascade pos: {pulse['cascade_position']})")
        
        # Small delay for readability
        time.sleep(0.5)
    
    # Test different locations
    test_locations = [
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
        {"name": "New York", "lat": 40.7128, "lon": -74.0060},
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    ]
    
    print("\nPulses for different locations at the same time:")
    
    for location in test_locations:
        # Generate pulse for this location
        pulse = generator.generate_pulse(
            location["lat"], 
            location["lon"], 
            sunset_time,  # Using same sunset time for simplicity
            current_time
        )
        
        # Print pulse hash
        print(f"  {location['name']}: {pulse['pulse_hash']}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
