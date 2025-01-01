import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.visualization.chart import ChartWindow
from datetime import datetime, timedelta

class TestChartWindow(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.sample_data = [
            {
                'timestamp': datetime.now() - timedelta(minutes=15),
                'volume_percent': 25.5
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=10),
                'volume_percent': 26.2
            },
            {
                'timestamp': datetime.now() - timedelta(minutes=5),
                'volume_percent': 24.8
            }
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    @patch('matplotlib.figure.Figure')
    @patch('matplotlib.backends.backend_tkagg.FigureCanvasTkAgg')
    def test_chart_creation(self, mock_canvas, mock_figure):
        """Test that chart window is created with correct data."""
        # Mock figure and canvas
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        mock_ax = MagicMock()
        mock_fig.add_subplot.return_value = mock_ax
        
        # Create chart window
        chart = ChartWindow(self.root, "Bitcoin", self.sample_data)
        
        # Verify chart setup
        mock_figure.assert_called_once()
        mock_ax.set_xlabel.assert_called_with('Time')
        mock_ax.set_ylabel.assert_called_with('Volume %')
        mock_ax.grid.assert_called_with(True)
        
        # Verify data plotting
        mock_ax.plot.assert_called_once()
        args = mock_ax.plot.call_args[0]
        self.assertEqual(len(args[0]), len(self.sample_data))  # x values
        self.assertEqual(len(args[1]), len(self.sample_data))  # y values
    
    def test_zoom_functionality(self):
        """Test zoom event handling."""
        chart = ChartWindow(self.root, "Bitcoin", self.sample_data)
        
        # Create mock scroll event
        event = MagicMock()
        event.button = 'up'
        event.xdata = 1.0
        event.ydata = 25.0
        
        # Mock axes
        mock_ax = MagicMock()
        event.inaxes = mock_ax
        mock_ax.get_xlim.return_value = (0, 2)
        mock_ax.get_ylim.return_value = (20, 30)
        
        # Test zoom in
        chart.on_scroll(event)
        mock_ax.set_xlim.assert_called_once()
        mock_ax.set_ylim.assert_called_once()
        mock_ax.figure.canvas.draw.assert_called_once()

if __name__ == '__main__':
    unittest.main()
