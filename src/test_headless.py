import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.scraper.market_scraper import MarketScraper
from src.storage.data_store import DataStore
from src.gui.main_window import MainWindow
import tkinter as tk

class TestHeadlessFunctionality(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.root = MagicMock(spec=tk.Tk)
        self.data_store = DataStore()
        self.scraper = MarketScraper()
        self.scraper.fetch_data = MagicMock(return_value=[
            {"name": "Bitcoin", "price": "$50000", "volume_percent": 25.5},
            {"name": "Ethereum", "price": "$3000", "volume_percent": 15.2}
        ])
        self.window = MainWindow(self.root, self.scraper, self.data_store, testing_mode=True)

    def test_data_scraping(self):
        """Test data scraping functionality."""
        # Verify scraper returns correctly formatted data
        data = self.scraper.fetch_data()
        self.assertEqual(len(data), 2)
        self.assertIn("name", data[0])
        self.assertIn("price", data[0])
        self.assertIn("volume_percent", data[0])

    def test_auto_refresh_timing(self):
        """Test auto-refresh timing logic."""
        # Mock time.sleep to avoid waiting
        with patch('time.sleep') as mock_sleep:
            # Start auto-refresh in testing mode
            self.window.scraper.start_auto_refresh(lambda x: None, testing=True)
            
            # Verify auto-refresh interval is set to 5 minutes
            mock_sleep.assert_called_once_with(300)  # 300 seconds = 5 minutes

    def test_data_storage(self):
        """Test historical data storage."""
        # Add test data points
        self.data_store.add_data_point("Bitcoin", 25.5, datetime.now())
        self.data_store.add_data_point("Bitcoin", 26.0, datetime.now() + timedelta(minutes=5))
        
        # Verify data retrieval
        data = self.data_store.get_historical_data("Bitcoin")
        self.assertEqual(len(data), 2)
        self.assertTrue(all(isinstance(d, dict) for d in data))
        self.assertTrue(all("timestamp" in d and "volume_percent" in d for d in data))

    def test_manual_refresh(self):
        """Test manual refresh functionality."""
        initial_call_count = self.scraper.fetch_data.call_count
        self.window.refresh_data()
        self.assertEqual(self.scraper.fetch_data.call_count, initial_call_count + 1)

    def test_data_formatting(self):
        """Test data column formatting."""
        self.window.refresh_data()
        # Get the data that would be displayed
        displayed_data = self.scraper.fetch_data()
        # Verify column format
        first_item = displayed_data[0]
        self.assertIsInstance(first_item["name"], str)
        self.assertIsInstance(first_item["price"], str)
        self.assertIsInstance(first_item["volume_percent"], (int, float))

if __name__ == '__main__':
    unittest.main()
