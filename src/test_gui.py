import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from datetime import datetime, timedelta
import time
import os
from xvfbwrapper import Xvfb
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.visualization.chart import ChartWindow
from src.gui.main_window import MainWindow
from src.scraper.market_scraper import MarketScraper
from src.storage.data_store import DataStore

def run_gui_manually():
    """Run the GUI manually for visual testing."""
    root = tk.Tk()
    scraper = MarketScraper()
    data_store = DataStore()
    app = MainWindow(root, scraper, data_store)
    root.mainloop()

class TestGUIFunctionality(unittest.TestCase):
    """Test suite for GUI functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up virtual display for GUI testing."""
        cls.vdisplay = Xvfb()
        cls.vdisplay.start()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up virtual display."""
        cls.vdisplay.stop()
    
    def setUp(self):
        """Set up test environment."""
        self.root = None  # No GUI in testing mode
        self.scraper = MarketScraper()
        self.data_store = DataStore()
        
        # Mock scraper data
        self.mock_data = [
            {"name": "Bitcoin", "price": 50000.0, "volume_percent": 25.5, "timestamp": datetime.now()},
            {"name": "Ethereum", "price": 3000.0, "volume_percent": 15.2, "timestamp": datetime.now()}
        ]
        self.scraper.fetch_data = MagicMock(return_value=self.mock_data)
        
        # Create historical data
        for i in range(5):
            timestamp = datetime.now() - timedelta(minutes=5*i)
            for crypto in self.mock_data:
                self.data_store.add_data_point(
                    crypto["name"],
                    crypto["volume_percent"] + i,  # Vary the volume percentage
                    timestamp
                )
        
        # Initialize window in testing mode
        self.window = MainWindow(None, self.scraper, self.data_store, testing_mode=True)

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'window'):
            self.window.on_closing()
        
    def test_chart_display(self):
        """Test that clicking a cryptocurrency opens the chart window."""
        # First ensure we have data
        data = self.window.refresh_data()
        self.assertIsNotNone(data)
        self.assertTrue(len(data) > 0)
        
        # Verify the first cryptocurrency data
        first_crypto = data[0]
        self.assertEqual(first_crypto["name"], "Bitcoin")
        
        # Get historical data
        historical_data = self.data_store.get_historical_data("Bitcoin")
        self.assertTrue(len(historical_data) > 0)
        
        # Create chart window in testing mode
        chart_window = ChartWindow(None, "Bitcoin", historical_data, testing_mode=True)
        self.assertIsNotNone(chart_window)
        self.assertTrue(hasattr(chart_window, 'ax'))
        self.assertEqual(len(chart_window.timestamps), len(historical_data))
        
    def test_data_columns(self):
        """Test that data columns are displayed correctly."""
        # Get data directly
        data = self.window.refresh_data()
        self.assertIsNotNone(data)
        self.assertTrue(len(data) > 0)
        
        # Verify column headers match requirements
        expected_headers = ["Cryptocurrency Name", "Current Price", "Trading Volume Percentage (Volume %)"]
        actual_headers = self.window.get_column_headers()
        self.assertEqual(actual_headers, expected_headers)
        
        # Verify data formatting
        first_item = data[0]
        # Test cryptocurrency name
        self.assertEqual(first_item["name"], "Bitcoin")
        
        # Test price formatting
        price_str = self.window.format_price(first_item["price"])
        self.assertTrue(price_str.startswith("$"))
        self.assertTrue(price_str.replace("$", "").replace(",", "").replace(".", "").isdigit())
        
        # Test volume percentage formatting
        volume_str = self.window.format_volume(first_item["volume_percent"])
        self.assertTrue(volume_str.endswith("%"))
        self.assertTrue(float(volume_str.rstrip("%")) >= 0)
        
    def test_chart_zoom(self):
        """Test chart zoom functionality."""
        # Create sample historical data
        historical_data = []
        current_time = time.time()
        for i in range(5):
            timestamp = current_time - i * 300  # 5-minute intervals
            historical_data.append({
                "timestamp": timestamp,
                "volume_percent": 25.0 + i
            })
            
        # Create chart window in testing mode
        chart_window = ChartWindow(None, "Bitcoin", historical_data, testing_mode=True)
        
        # Verify chart was created
        self.assertIsNotNone(chart_window)
        self.assertTrue(hasattr(chart_window, 'ax'))
        
        # Get initial x limits
        initial_xlim = chart_window.ax.get_xlim()
        
        # Test zoom in
        chart_window.zoom_in()
        zoomed_in_xlim = chart_window.ax.get_xlim()
        self.assertGreater(initial_xlim[1] - initial_xlim[0],
                          zoomed_in_xlim[1] - zoomed_in_xlim[0],
                          "Zoom in should decrease the visible range")
        
        # Test zoom out
        chart_window.zoom_out()
        zoomed_out_xlim = chart_window.ax.get_xlim()
        self.assertGreater(zoomed_out_xlim[1] - zoomed_out_xlim[0],
                          zoomed_in_xlim[1] - zoomed_in_xlim[0],
                          "Zoom out should increase the visible range")
        
    def test_auto_refresh_display(self):
        """Test that auto-refresh updates the display."""
        # Get initial data
        initial_data = self.window.refresh_data()
        self.assertIsNotNone(initial_data)
        
        # Mock new data
        new_data = [
            {"name": "Bitcoin", "price": 51000.0, "volume_percent": 26.5, "timestamp": datetime.now()},
            {"name": "Ethereum", "price": 3100.0, "volume_percent": 16.2, "timestamp": datetime.now()}
        ]
        self.scraper.fetch_data = MagicMock(return_value=new_data)
        
        # Trigger refresh and get updated data
        updated_data = self.window.refresh_data()
        
        # Verify data was updated
        self.assertEqual(len(updated_data), len(new_data))
        first_item = updated_data[0]
        self.assertEqual(first_item["price"], 51000.0)
        self.assertEqual(first_item["volume_percent"], 26.5)

if __name__ == '__main__':
    # If run directly, allow choosing between manual GUI testing and unit tests
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        run_gui_manually()
    else:
        unittest.main()
