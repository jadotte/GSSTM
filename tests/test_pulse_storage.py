import sys
import os
import uuid
import time
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pulse_storage import PulseStorage
if __name__ == "__main__":
    storage = PulseStorage(local_backup_dir='pulse_backups')
    
    pulse = {
        'id': str(uuid.uuid4()),
        'timestamp': time.time(),
        'latitude': 37.7749,
        'longitude': -122.4194,
        'pulse_hash': 'abcdef1234567890',
    }
    
    aircraft = [
        {
            'icao24': 'abc123',
            'callsign': 'UAL123',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'altitude': 10000,
            'plus_code': '849VQHM5+XM',
        },
        {
            'icao24': 'def456',
            'callsign': 'DAL456',
            'latitude': 37.8, 
            'longitude': -122.5,
            'altitude': 8000,
            'plus_code': '849VQHF6+7R',
        },
    ]
    
    result = storage.store_pulse(pulse, aircraft)
    print("Storage result:", json.dumps(result, indent=2))
    
    anomaly = {
        'type': 'missed_pulse',
        'expected_time': time.time() - 1,
        'actual_time': time.time(),
        'description': 'Pulse delayed',
    }
    storage.log_anomaly(anomaly)
    print("Logged anomaly")

    print("\nStorage stats:", json.dumps(storage.get_stats(), indent=2))
