"""Database module for cryptocurrency market data storage."""
import os
import sqlite3
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CryptoDatabase:
    """Handles all database operations for cryptocurrency data."""
    
    def __init__(self, db_path: str = "crypto_data.db"):
        """Initialize database connection and create tables if they don't exist.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.initialize_db()
    
    def initialize_db(self) -> None:
        """Create necessary database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create main cryptocurrency data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crypto_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        rank INTEGER NOT NULL,
                        price REAL NOT NULL,
                        volume_percentage REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index on timestamp for faster querying
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON crypto_data(timestamp)
                ''')
                
                # Create index on name and timestamp for faster historical data retrieval
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_name_timestamp 
                    ON crypto_data(name, timestamp)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_crypto_data(self, cryptos: List[Dict]) -> None:
        """Insert cryptocurrency data into the database.
        
        Args:
            cryptos: List of dictionaries containing cryptocurrency data
                    Each dict should have: name, rank, price, volume_percentage
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    '''
                    INSERT INTO crypto_data (name, rank, price, volume_percentage)
                    VALUES (:name, :rank, :price, :volume_percentage)
                    ''',
                    cryptos
                )
                conn.commit()
                logger.debug(f"Inserted {len(cryptos)} cryptocurrency records")
        except sqlite3.Error as e:
            logger.error(f"Error inserting crypto data: {e}")
            raise
    
    def get_top_n_cryptos(self, n: int = 10) -> List[Dict]:
        """Get the top N cryptocurrencies by rank from the latest data.
        
        Args:
            n: Number of top cryptocurrencies to retrieve
        
        Returns:
            List of dictionaries containing cryptocurrency data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(
                    '''
                    SELECT name, rank, price, volume_percentage, timestamp
                    FROM crypto_data
                    WHERE timestamp = (
                        SELECT MAX(timestamp) FROM crypto_data
                    )
                    ORDER BY rank
                    LIMIT ?
                    ''',
                    (n,)
                )
                
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving top {n} cryptos: {e}")
            raise
    
    def get_crypto_history(self, name: str, hours: int = 24) -> List[Dict]:
        """Get historical data for a specific cryptocurrency.
        
        Args:
            name: Name of the cryptocurrency
            hours: Number of hours of historical data to retrieve
        
        Returns:
            List of dictionaries containing historical data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                time_threshold = datetime.now() - timedelta(hours=hours)
                
                cursor.execute(
                    '''
                    SELECT name, rank, price, volume_percentage, timestamp
                    FROM crypto_data
                    WHERE name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    ''',
                    (name, time_threshold)
                )
                
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving history for {name}: {e}")
            raise
    
    def cleanup_old_data(self, hours: int = 48) -> None:
        """Remove data older than specified hours to maintain minimal DB size.
        
        Args:
            hours: Number of hours of data to keep
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                time_threshold = datetime.now() - timedelta(hours=hours)
                
                cursor.execute(
                    'DELETE FROM crypto_data WHERE timestamp < ?',
                    (time_threshold,)
                )
                
                deleted_rows = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_rows} old records")
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            raise
    
    def get_last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the most recent data update.
        
        Returns:
            datetime object of the last update or None if no data exists
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT MAX(timestamp) FROM crypto_data')
                result = cursor.fetchone()
                return datetime.fromisoformat(result[0]) if result[0] else None
        except sqlite3.Error as e:
            logger.error(f"Error getting last update time: {e}")
            raise

    def get_previous_top_n(self, n: int = 10) -> List[Dict]:
        """Get the previous top N cryptocurrencies by volume percentage.
        
        Args:
            n: Number of top cryptocurrencies to retrieve (default: 10)
            
        Returns:
            List of dictionaries containing cryptocurrency data from the previous update
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get the latest timestamp
                cursor.execute('SELECT MAX(timestamp) FROM crypto_data')
                latest_timestamp = cursor.fetchone()[0]
                
                if not latest_timestamp:
                    return []
                
                # Get the previous timestamp
                cursor.execute('''
                    SELECT MAX(timestamp) 
                    FROM crypto_data 
                    WHERE timestamp < ?
                ''', (latest_timestamp,))
                prev_timestamp = cursor.fetchone()[0]
                
                if not prev_timestamp:
                    return []
                
                # Get the top N cryptocurrencies from the previous timestamp
                cursor.execute('''
                    SELECT name, rank, price, volume_percentage
                    FROM crypto_data
                    WHERE timestamp = ?
                    ORDER BY volume_percentage DESC
                    LIMIT ?
                ''', (prev_timestamp, n))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting previous top {n}: {e}")
            return []
