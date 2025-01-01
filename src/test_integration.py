import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from src.scraper.market_scraper import MarketScraper
from src.storage.data_store import DataStore
from src.gui.main_window import MainWindow

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment with mocked components."""
        self.root = MagicMock()
        self.data_store = DataStore()
        
        # Mock scraper with sample data
        self.sample_data = [
            {
                "name": "Bitcoin",
                "price": 50000.0,
                "volume_percent": 25.5,
                "timestamp": datetime.now()
            },
            {
                "name": "Ethereum",
                "price": 3000.0,
                "volume_percent": 15.2,
                "timestamp": datetime.now()
            }
        ]
        
        # Create and configure scraper mock
        self.scraper = MagicMock()
        self.scraper.fetch_data = MagicMock(return_value=self.sample_data)
        self.scraper.start_auto_refresh = MagicMock()
        self.scraper.stop_auto_refresh = MagicMock()
        
        # Create main window with mocked components
        with patch('tkinter.ttk.Treeview') as mock_tree:
            with patch('tkinter.ttk.Button'):
                with patch('tkinter.ttk.Label'):
                    self.window = MainWindow(self.root, self.scraper, self.data_store, testing_mode=True)
                    # Configure tree mock
                    self.window.tree = mock_tree
    
    def test_data_flow(self):
        """Test data flows correctly from scraper through storage to GUI."""
        # Reset mocks to clear setup calls
        self.scraper.fetch_data.reset_mock()
        
        # Trigger data refresh
        self.window.refresh_data()
        
        # Verify scraper was called exactly once
        self.scraper.fetch_data.assert_called_once()
        
        # Verify data was stored
        for item in self.sample_data:
            historical_data = self.data_store.get_historical_data(item["name"])
            self.assertTrue(len(historical_data) > 0)
            latest_point = historical_data[-1]
            self.assertEqual(latest_point["volume_percent"], item["volume_percent"])
    
    def test_auto_refresh(self):
        """Test auto-refresh mechanism."""
        with patch('time.sleep', return_value=None):
            # Start auto-refresh
            self.window.start_auto_refresh()
            
            # Verify initial data load
            self.scraper.fetch_data.assert_called()
            
            # Reset mock and simulate time passage
            self.scraper.fetch_data.reset_mock()
            
            # Simulate auto-refresh by directly calling refresh_data
            self.window.refresh_data()
            
            # Verify data was updated
            self.scraper.fetch_data.assert_called_once()
            self.assertTrue(len(self.data_store.get_historical_data("Bitcoin")) > 0)
    
    def test_chart_integration(self):
        """Test chart creation with stored data."""
        # Add historical data points with proper format
        for i in range(5):
            timestamp = datetime.now() - timedelta(minutes=5*i)
            self.data_store.add_data_point(
                "Bitcoin",
                25.5 - i,  # Decreasing volume percentage
                timestamp
            )
            
        # Verify historical data exists and has correct format
        historical_data = self.data_store.get_historical_data("Bitcoin")
        self.assertTrue(len(historical_data) > 0)
        self.assertTrue(all(isinstance(d, dict) for d in historical_data))
        self.assertTrue(all("timestamp" in d and "volume_percent" in d for d in historical_data))
        
        # Reset mocks after initial data setup
        self.scraper.fetch_data.reset_mock()
        
        # Create a mock event
        mock_event = MagicMock()
        mock_event.x = 100
        mock_event.y = 100
        
        # Patch both the import and usage locations of ChartWindow
        with patch('src.visualization.chart.ChartWindow') as mock_chart, \
             patch('src.gui.main_window.ChartWindow', mock_chart):
            # Configure tree mock for chart creation
            # Mock tree.identify to return "cell" when called with "region"
            def identify_side_effect(*args):
                print(f"identify called with args: {args}")  # Debug print
                if len(args) == 3 and args[0] == "region":
                    return "cell"  # Return "cell" to indicate clicking on data
                return None
            self.window.tree.identify.side_effect = identify_side_effect
            
            # Configure selection and item values
            self.window.tree.selection.return_value = ['item1']
            self.window.tree.item.return_value = {'values': ['Bitcoin', '$50000.00', '25.50%']}
            
            # Trigger chart creation
            self.window.on_item_click(mock_event)
            
            # Debug prints
            print(f"identify calls: {self.window.tree.identify.mock_calls}")
            print(f"selection calls: {self.window.tree.selection.mock_calls}")
            print(f"item calls: {self.window.tree.item.mock_calls}")
            print(f"ChartWindow calls: {mock_chart.mock_calls}")
            
            # Verify identify was called with correct arguments
            self.window.tree.identify.assert_any_call("region", mock_event.x, mock_event.y)
            
            # Verify selection and item were called
            self.window.tree.selection.assert_called_once()
            self.window.tree.item.assert_called_once_with('item1')
            
            # Verify chart was created with correct data
            mock_chart.assert_called_once()
            args = mock_chart.call_args[0]
            self.assertEqual(len(args), 4, "ChartWindow should be called with 4 arguments")
            self.assertEqual(args[1], "Bitcoin", "Second argument should be crypto name")
            self.assertTrue(len(args[2]) > 0, "Historical data should not be empty")
            self.assertTrue(args[3], "Testing mode should be True")
            
    def test_manual_refresh(self):
        """Test manual refresh functionality."""
        # Reset fetch_data mock to clear any previous calls
        self.scraper.fetch_data.reset_mock()
        
        # Trigger manual refresh
        self.window.refresh_data()
        
        # Verify data was fetched
        self.scraper.fetch_data.assert_called_once()
        
        # Verify table was updated
        self.assertTrue(len(self.data_store.get_historical_data("Bitcoin")) > 0)

if __name__ == '__main__':
    unittest.main()
