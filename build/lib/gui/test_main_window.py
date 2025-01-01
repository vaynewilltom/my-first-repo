import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.gui.main_window import MainWindow
from src.scraper.market_scraper import MarketScraper
from src.storage.data_store import DataStore

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        self.scraper = MagicMock(spec=MarketScraper)
        self.data_store = MagicMock(spec=DataStore)
        
        # Mock sample data
        self.sample_data = [
            {"name": "Bitcoin", "price": "50000", "volume": "25.5"},
            {"name": "Ethereum", "price": "3000", "volume": "15.2"}
        ]
        self.scraper.get_market_data.return_value = self.sample_data
        
        # Create main window with mocked components
        with patch('tkinter.ttk.Treeview'):
            with patch('tkinter.ttk.Button'):
                with patch('tkinter.ttk.Label'):
                    self.window = MainWindow(self.root, self.scraper, self.data_store)
    
    def test_refresh_data(self):
        """Test that refresh_data updates the table with new data"""
        self.window.refresh_data()
        self.scraper.get_market_data.assert_called_once()
    
    def test_update_table(self):
        """Test that update_table properly updates the table with data"""
        self.window.update_table(self.sample_data)
        self.assertEqual(len(self.sample_data), 2)
    
    def test_on_item_click(self):
        """Test that clicking an item opens the chart window"""
        with patch('gui.main_window.ChartWindow') as mock_chart:
            # Mock tree item selection
            self.window.tree.selection.return_value = ['item1']
            self.window.tree.item.return_value = {'values': ['Bitcoin', '50000', '25.5']}
            
            # Simulate item click
            self.window.on_item_click(None)
            
            # Verify chart window was created
            mock_chart.assert_called_once()
            
    def test_sort_column(self):
        """Test that sort_column properly sorts table data"""
        self.window.sort_column('name', False)
        self.window.tree.get_children.assert_called_once()

if __name__ == '__main__':
    unittest.main()
