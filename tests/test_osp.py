import sys
import os
import json
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from osp import PulseGenerator

if __name__ == "__main__":
    generator = PulseGenerator()

    # Test location (San Francisco)
    lat, lon = 37.7749, -122.4194

    current_time = datetime.now(timezone.utc)
    sunset_time = current_time.replace(hour=current_time.hour - 1)

    pulse = generator.generate_pulse(lat, lon, sunset_time, current_time)

    print("Generated Pulse:")
    print(json.dumps(pulse, indent=2))

    from datetime import timedelta

    next_time = current_time + timedelta(seconds=1)
    pulse2 = generator.generate_pulse(lat, lon, sunset_time, next_time)

    print("\nGenerated Pulse (1 second later):")
    print(json.dumps(pulse2, indent=2))

    print("\nPulses are different:", pulse["pulse_hash"] != pulse2["pulse_hash"])
