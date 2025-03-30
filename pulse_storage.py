import json
import time
import os
import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

class PulseStorage:
    """
    Store and log pulse events on AWS
    """
    
    def __init__(self, dynamodb_table=None, s3_bucket=None, local_backup_dir='pulses'):
        """
        Initialize the pulse storage system
        
        Args:
            dynamodb_table: DynamoDB table name for storing pulses
            s3_bucket: S3 bucket name for storing pulse data
            local_backup_dir: Local directory for storing backups when AWS is unavailable
        """
        self.dynamodb_table = dynamodb_table
        self.s3_bucket = s3_bucket
        self.local_backup_dir = local_backup_dir
        
        # Create local backup directory if it doesn't exist
        os.makedirs(local_backup_dir, exist_ok=True)
        
        # Initialize AWS clients if table/bucket names are provided
        self.dynamodb = boto3.resource('dynamodb') if dynamodb_table else None
        self.s3 = boto3.client('s3') if s3_bucket else None
        
        # Keep track of successful and failed operations
        self.stats = {
            'dynamodb_success': 0,
            'dynamodb_errors': 0,
            's3_success': 0,
            's3_errors': 0,
            'local_backups': 0,
        }
    
    def store_pulse(self, pulse_data, aircraft_data=None):
        """
        Store a pulse event and associated aircraft data
        
        Args:
            pulse_data: Dictionary containing pulse information
            aircraft_data: Optional list of aircraft positions associated with the pulse
        
        Returns:
            Dictionary with storage results
        """
        timestamp = datetime.now(timezone.utc)
        result = {
            'timestamp': timestamp.isoformat(),
            'dynamodb': False,
            's3': False,
            'local': False,
        }
        
        # Create a complete record with pulse and aircraft data
        complete_record = {
            'pulse': pulse_data,
            'timestamp': timestamp.isoformat(),
            'aircraft': aircraft_data or [],
        }
        
        # Try to store in DynamoDB
        if self.dynamodb_table:
            try:
                table = self.dynamodb.Table(self.dynamodb_table)
                
                # Create DynamoDB item
                item = {
                    'PulseId': pulse_data.get('id', str(uuid.uuid4())),
                    'Timestamp': int(timestamp.timestamp() * 1000),  # Milliseconds since epoch
                    'PulseData': json.dumps(pulse_data),
                    'AircraftCount': len(aircraft_data or []),
                }
                
                # Add TTL for automatic expiration (30 days)
                item['TTL'] = int(timestamp.timestamp() + 30 * 24 * 60 * 60)
                
                # Store in DynamoDB
                table.put_item(Item=item)
                
                result['dynamodb'] = True
                self.stats['dynamodb_success'] += 1
                
            except Exception as e:
                print(f"DynamoDB storage error: {e}")
                self.stats['dynamodb_errors'] += 1
        
        # Try to store in S3
        if self.s3_bucket:
            try:
                # Create S3 key with date-based partitioning
                date_part = timestamp.strftime('%Y/%m/%d/%H')
                s3_key = f"pulses/{date_part}/{pulse_data.get('id', uuid.uuid4())}.json"
                
                # Convert the complete record to JSON
                json_data = json.dumps(complete_record)
                
                # Upload to S3
                self.s3.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=json_data,
                    ContentType='application/json',
                )
                
                result['s3'] = True
                self.stats['s3_success'] += 1
                
            except Exception as e:
                print(f"S3 storage error: {e}")
                self.stats['s3_errors'] += 1
        
        # Always store a local backup
        try:
            # Create a timestamped filename
            filename = f"{pulse_data.get('id', uuid.uuid4())}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.local_backup_dir, filename)
            
            # Write to local file
            with open(filepath, 'w') as f:
                json.dump(complete_record, f)
            
            result['local'] = True
            self.stats['local_backups'] += 1
            
        except Exception as e:
            print(f"Local backup error: {e}")
        
        return result
    
    def log_anomaly(self, anomaly_data):
        """
        Log an anomaly or missed pulse
        
        Args:
            anomaly_data: Dictionary describing the anomaly
        """
        timestamp = datetime.now(timezone.utc)
        
        # Ensure the anomaly data has a timestamp
        if 'timestamp' not in anomaly_data:
            anomaly_data['timestamp'] = timestamp.isoformat()
        
        # Add an ID if not present
        if 'id' not in anomaly_data:
            anomaly_data['id'] = str(uuid.uuid4())
        
        # Log to DynamoDB if available
        if self.dynamodb_table:
            try:
                table = self.dynamodb.Table(self.dynamodb_table)
                
                # Create DynamoDB item
                item = {
                    'PulseId': f"anomaly_{anomaly_data['id']}",
                    'Timestamp': int(timestamp.timestamp() * 1000),  # Milliseconds since epoch
                    'AnomalyData': json.dumps(anomaly_data),
                    'IsAnomaly': True,
                }
                
                # Add TTL for automatic expiration (30 days)
                item['TTL'] = int(timestamp.timestamp() + 30 * 24 * 60 * 60)
                
                # Store in DynamoDB
                table.put_item(Item=item)
                
            except Exception as e:
                print(f"DynamoDB anomaly logging error: {e}")
        
        # Always log locally
        try:
            # Create anomalies directory if it doesn't exist
            anomalies_dir = os.path.join(self.local_backup_dir, 'anomalies')
            os.makedirs(anomalies_dir, exist_ok=True)
            
            # Create a timestamped filename
            filename = f"anomaly_{anomaly_data['id']}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(anomalies_dir, filename)
            
            # Write to local file
            with open(filepath, 'w') as f:
                json.dump(anomaly_data, f)
            
        except Exception as e:
            print(f"Local anomaly logging error: {e}")
    
    def get_stats(self):
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        return self.stats
    
    def cleanup_old_backups(self, max_age_days=7):
        """
        Clean up old local backups
        
        Args:
            max_age_days: Maximum age of local backups in days
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        # Process regular pulse backups
        for filename in os.listdir(self.local_backup_dir):
            filepath = os.path.join(self.local_backup_dir, filename)
            
            # Skip directories and non-JSON files
            if os.path.isdir(filepath) or not filename.endswith('.json'):
                continue
            
            # Check file age
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                try:
                    os.remove(filepath)
                    print(f"Removed old backup: {filename}")
                except Exception as e:
                    print(f"Error removing old backup {filename}: {e}")
        
        # Process anomaly logs
        anomalies_dir = os.path.join(self.local_backup_dir, 'anomalies')
        if os.path.exists(anomalies_dir):
            for filename in os.listdir(anomalies_dir):
                filepath = os.path.join(anomalies_dir, filename)
                
                # Skip directories and non-JSON files
                if os.path.isdir(filepath) or not filename.endswith('.json'):
                    continue
                
                # Check file age
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        print(f"Removed old anomaly log: {filename}")
                    except Exception as e:
                        print(f"Error removing old anomaly log {filename}: {e}")


