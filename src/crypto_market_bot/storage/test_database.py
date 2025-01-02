"""Tests for the database module."""
import os
import unittest
from datetime import datetime, timedelta
from .database import CryptoDatabase

class TestCryptoDatabase(unittest.TestCase):
    """Test cases for CryptoDatabase class."""
    
    def setUp(self):
        """Set up test database."""
        self.test_db_path = "test_crypto_data.db"
        self.db = CryptoDatabase(self.test_db_path)
        
        # Sample crypto data for testing
        self.sample_data = [
            {
                "name": "Bitcoin",
                "rank": 1,
                "price": 50000.0,
                "volume_percentage": 25.5
            },
            {
                "name": "Ethereum",
                "rank": 2,
                "price": 3000.0,
                "volume_percentage": 15.3
            }
        ]
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_insert_and_retrieve_crypto_data(self):
        """Test inserting and retrieving cryptocurrency data."""
        self.db.insert_crypto_data(self.sample_data)
        top_cryptos = self.db.get_top_n_cryptos(2)
        
        self.assertEqual(len(top_cryptos), 2)
        self.assertEqual(top_cryptos[0]["name"], "Bitcoin")
        self.assertEqual(top_cryptos[1]["name"], "Ethereum")
    
    def test_get_crypto_history(self):
        """Test retrieving historical data for a cryptocurrency."""
        self.db.insert_crypto_data(self.sample_data)
        history = self.db.get_crypto_history("Bitcoin")
        
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["name"], "Bitcoin")
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data from the database."""
        self.db.insert_crypto_data(self.sample_data)
        self.db.cleanup_old_data(hours=0)  # Clean all data
        
        top_cryptos = self.db.get_top_n_cryptos(2)
        self.assertEqual(len(top_cryptos), 0)
    
    def test_get_last_update_time(self):
        """Test getting the last update timestamp."""
        self.db.insert_crypto_data(self.sample_data)
        last_update = self.db.get_last_update_time()
        
        self.assertIsNotNone(last_update)
        self.assertIsInstance(last_update, datetime)
        self.assertLess(datetime.now() - last_update, timedelta(minutes=1))

if __name__ == '__main__':
    unittest.main()
