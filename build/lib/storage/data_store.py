from typing import List, Dict, Any
from datetime import datetime

class DataStore:
    def __init__(self):
        self.historical_data = {}  # Dictionary to store historical data in memory
        
    def add_data_point(self, crypto_name: str, volume_percent: float, timestamp: datetime):
        """Add a new data point for a cryptocurrency."""
        if crypto_name not in self.historical_data:
            self.historical_data[crypto_name] = []
        self.historical_data[crypto_name].append({
            'timestamp': timestamp,
            'volume_percent': volume_percent
        })
        
    def get_historical_data(self, crypto_name: str) -> List[Dict[str, Any]]:
        """Get historical data for a specific cryptocurrency."""
        return self.historical_data.get(crypto_name, [])
