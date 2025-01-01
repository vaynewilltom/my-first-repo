import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Any

class ChartWindow:
    def __init__(self, parent: tk.Tk | None, crypto_name: str, historical_data: List[Dict[str, Any]], testing_mode: bool = False):
        """Initialize chart window."""
        self.testing_mode = testing_mode
        self.parent = parent
        self.crypto_name = crypto_name
        
        if not testing_mode and parent is not None:
            self.window = tk.Toplevel(parent)
            self.window.title(f"{crypto_name} - Volume % History")
        else:
            self.window = None
            
        self.setup_chart(historical_data)
        
    def setup_chart(self, historical_data: List[Dict[str, Any]]):
        """Create and display the chart."""
        self.fig = Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111)
        
        # Extract data for plotting
        self.timestamps = [d['timestamp'] for d in historical_data]
        self.volumes = [d['volume_percent'] for d in historical_data]
        
        # Create the line plot
        self.ax.plot(self.timestamps, self.volumes)
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Volume %')
        self.ax.grid(True)
        
        if not self.testing_mode:
            # Enable zooming
            self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
            
            # Create canvas and add to window
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.window)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def zoom_in(self):
        """Programmatically zoom in for testing."""
        if self.testing_mode:
            self._zoom(scale_factor=0.9)  # Zoom in by reducing the view range
            
    def zoom_out(self):
        """Programmatically zoom out for testing."""
        if self.testing_mode:
            self._zoom(scale_factor=1.1)  # Zoom out by increasing the view range
            
    def _zoom(self, scale_factor):
        """Apply zoom with the given scale factor."""
        if not hasattr(self, 'ax'):
            return
            
        # Get the current limits
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # Calculate center points
        xcenter = (cur_xlim[0] + cur_xlim[1]) / 2
        ycenter = (cur_ylim[0] + cur_ylim[1]) / 2
        
        # Set new limits
        new_xlim = (
            xcenter - (xcenter - cur_xlim[0]) * scale_factor,
            xcenter + (cur_xlim[1] - xcenter) * scale_factor
        )
        new_ylim = (
            ycenter - (ycenter - cur_ylim[0]) * scale_factor,
            ycenter + (cur_ylim[1] - ycenter) * scale_factor
        )
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        
        if not self.testing_mode and hasattr(self, 'canvas'):
            self.canvas.draw()
            
    def on_scroll(self, event):
        """Handle zoom events."""
        ax = event.inaxes
        if ax is None:
            return
            
        # Get the cursor position
        xdata = event.xdata
        ydata = event.ydata
        
        if event.button == 'up':
            self.zoom_in()
        else:
            self.zoom_out()
