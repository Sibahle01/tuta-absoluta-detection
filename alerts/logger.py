"""
Event logging module for system events and detections
"""

import json
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import asdict


class EventLogger:
    """Base class for event logging"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.events = []
    
    def log(self, event: Dict) -> None:
        """Log an event"""
        event['timestamp'] = datetime.now().isoformat()
        self.events.append(event)
        self._write(event)
    
    def _write(self, event: Dict) -> None:
        """Write event to storage - override in subclass"""
        pass
    
    def get_events(self, last_n: Optional[int] = None) -> List[Dict]:
        """Get logged events"""
        if last_n:
            return self.events[-last_n:]
        return self.events
    
    def clear(self) -> None:
        """Clear all events"""
        self.events = []


class JSONLogger(EventLogger):
    """JSON file logger"""
    
    def __init__(self, log_dir: str = "logs", filename: str = "ipm_events.json"):
        super().__init__(log_dir)
        self.filename = self.log_dir / filename
        self._load_existing()
    
    def _load_existing(self):
        """Load existing events from file"""
        if self.filename.exists():
            try:
                with open(self.filename, 'r') as f:
                    self.events = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.events = []
    
    def _write(self, event: Dict) -> None:
        """Write event to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def export_csv(self, csv_filename: Optional[str] = None):
        """Export events to CSV"""
        if csv_filename is None:
            csv_filename = self.filename.stem + ".csv"
        
        csv_path = self.log_dir / csv_filename
        if not self.events:
            print("No events to export")
            return
        
        # Get all unique keys
        keys = set()
        for event in self.events:
            keys.update(event.keys())
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(self.events)
        
        print(f"✅ Exported {len(self.events)} events to {csv_path}")


class CSVLogger(EventLogger):
    """CSV file logger (appends to file)"""
    
    def __init__(self, log_dir: str = "logs", filename: str = "ipm_events.csv"):
        super().__init__(log_dir)
        self.filename = self.log_dir / filename
        self._init_file()
    
    def _init_file(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.filename.exists():
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'pest_count', 'temperature', 'humidity', 
                                'ppi', 'action', 'message'])
    
    def _write(self, event: Dict) -> None:
        """Append event to CSV file"""
        row = [
            event.get('timestamp', datetime.now().isoformat()),
            event.get('pest_count', 0),
            event.get('temperature', 0),
            event.get('humidity', 0),
            event.get('ppi', 0),
            event.get('action', 'unknown'),
            event.get('message', '')
        ]
        
        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def read_all(self) -> List[Dict]:
        """Read all events from CSV file"""
        events = []
        if not self.filename.exists():
            return events
        
        with open(self.filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row['pest_count'] = int(row['pest_count'])
                row['temperature'] = float(row['temperature'])
                row['humidity'] = float(row['humidity'])
                row['ppi'] = float(row['ppi'])
                events.append(row)
        
        return events


if __name__ == "__main__":
    print("=== Logger Test ===")
    
    # Test JSON logger
    json_logger = JSONLogger()
    json_logger.log({
        'pest_count': 5,
        'temperature': 25.5,
        'humidity': 60,
        'ppi': 0.75,
        'action': 'spray',
        'message': 'Critical infestation detected'
    })
    print(f"JSON logger: {len(json_logger.get_events())} events")
    
    # Test CSV logger
    csv_logger = CSVLogger()
    csv_logger.log({
        'pest_count': 3,
        'temperature': 26.0,
        'humidity': 55,
        'ppi': 0.45,
        'action': 'warning',
        'message': 'Warning level reached'
    })
    print(f"CSV logger: {len(csv_logger.read_all())} events in file")