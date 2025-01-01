import os
import sqlite3
from typing import List, Dict, Any
from datetime import datetime

class DataStore:
    def __init__(self, data_dir: str | None = None):
        """Initialize the data store with optional data directory for SQLite database."""
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'crypto_data.db') if data_dir else ':memory:'
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database and create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historical_data (
                    crypto_name TEXT,
                    volume_percent REAL,
                    timestamp DATETIME,
                    PRIMARY KEY (crypto_name, timestamp)
                )
            ''')
            conn.commit()

    def add_data_point(self, crypto_name: str, volume_percent: float, timestamp: datetime | float):
        """Add a new data point for a cryptocurrency."""
        if isinstance(timestamp, float):
            timestamp = datetime.fromtimestamp(timestamp)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO historical_data (crypto_name, volume_percent, timestamp)
                VALUES (?, ?, ?)
            ''', (crypto_name, volume_percent, timestamp))
            conn.commit()

    def get_historical_data(self, crypto_name: str) -> List[Dict[str, Any]]:
        """Get historical data for a specific cryptocurrency."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, volume_percent
                FROM historical_data
                WHERE crypto_name = ?
                ORDER BY timestamp DESC
                LIMIT 100
            ''', (crypto_name,))
            
            return [
                {
                    'timestamp': datetime.fromisoformat(str(row[0])),
                    'volume_percent': row[1]
                }
                for row in cursor.fetchall()
            ]
