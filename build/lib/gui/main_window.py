import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any
import time
from ..visualization.chart import ChartWindow
from ..scraper.market_scraper import MarketScraper
from ..storage.data_store import DataStore

class MainWindow:
    COLUMN_HEADERS = [
        "Cryptocurrency Name",
        "Current Price",
        "Trading Volume Percentage (Volume %)"
    ]
    
    def __init__(self, root: tk.Tk | None, scraper: MarketScraper, data_store: DataStore, testing_mode: bool = False):
        self.root = root
        self.scraper = scraper
        self.data_store = data_store
        self.testing_mode = testing_mode
        
        self.tree = None
        if not testing_mode and root is not None:
            self.root.title("Crypto Market Data")
            self.root.geometry("800x600")
            self.setup_ui()
            # Bind closing event
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.start_auto_refresh()
        
    def setup_ui(self):
        """Setup the main window UI components."""
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Top 10 Cryptocurrencies by Volume", 
                              font=('Helvetica', 14, 'bold'))
        title_label.pack(pady=10)
        
        # Create frame for table with scrollbar
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Table for displaying crypto data
        self.tree = ttk.Treeview(table_frame, columns=("Name", "Price", "Volume %"), 
                                show="headings", height=10,
                                yscrollcommand=scrollbar.set)
        
        # Configure columns
        self.tree.heading("Name", text=self.COLUMN_HEADERS[0], command=lambda: self.sort_column("Name", False))
        self.tree.heading("Price", text=self.COLUMN_HEADERS[1], command=lambda: self.sort_column("Price", False))
        self.tree.heading("Volume %", text=self.COLUMN_HEADERS[2], command=lambda: self.sort_column("Volume %", False))
        
        self.tree.column("Name", width=200, anchor=tk.W)
        self.tree.column("Price", width=150, anchor=tk.E)
        self.tree.column("Volume %", width=150, anchor=tk.E)
        
        # Configure scrollbar
        scrollbar.config(command=self.tree.yview)
        
        # Pack table
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind click event
        self.tree.bind('<ButtonRelease-1>', self.on_item_click)
        
        # Control frame for buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="Refresh Now", command=self.refresh_data)
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.pack(pady=5)
        
    def get_column_headers(self):
        """Get the column headers for the data table."""
        return self.COLUMN_HEADERS
    
    def format_price(self, price: float) -> str:
        """Format price with currency symbol and commas."""
        return f"${price:,.2f}"
    
    def format_volume(self, volume: float) -> str:
        """Format volume percentage with % symbol."""
        return f"{volume:.2f}%"
    
    def refresh_data(self):
        """Fetch new data and update the display."""
        data = self.scraper.fetch_data()
        if not self.testing_mode:
            self.status_label.config(text="Refreshing data...")
            self.update_table(data)
            self.status_label.config(text=f"Last updated: {time.strftime('%H:%M:%S')}")
        return data  # Return data for testing
        
    def update_table(self, data: List[Dict[str, Any]]):
        """Update the table with new data."""
        if self.tree is not None:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Add new items
            for item in data:
                self.tree.insert("", tk.END, values=(
                    item["name"],
                    self.format_price(item['price']),
                    self.format_volume(item['volume_percent'])
                ))
        
        # Store the data points regardless of UI
        for item in data:
            self.data_store.add_data_point(
                item["name"],
                item["volume_percent"],
                item.get("timestamp", time.time())
            )
    
    def on_item_click(self, event):
        """Handle click events on table items."""
        if self.tree is None:
            return
            
        region = self.tree.identify("region", event.x, event.y)
        if not region or region == "heading":  # Skip if clicking on header or no region
            return
            
        item = self.tree.selection()
        if not item:
            return
            
        values = self.tree.item(item[0])["values"]
        if values:
            crypto_name = values[0]
            historical_data = self.data_store.get_historical_data(crypto_name)
            if historical_data:  # Only create chart if we have data
                ChartWindow(self.root, crypto_name, historical_data, testing_mode=self.testing_mode)
    
    def sort_column(self, column: str, reverse: bool):
        """Sort table by column."""
        if self.tree is None:
            return
            
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # Convert string values to appropriate types for sorting
        if column == "Price":
            items = [(float(value.replace('$', '').replace(',', '')), item) for value, item in items]
        elif column == "Volume %":
            items = [(float(value.replace('%', '')), item) for value, item in items]
            
        items.sort(reverse=reverse)
        
        # Rearrange items in sorted positions
        for index, (_, item) in enumerate(items):
            self.tree.move(item, '', index)
            
        # Reverse sort next time
        self.tree.heading(column, command=lambda: self.sort_column(column, not reverse))
    
    def start_auto_refresh(self):
        """Start the auto-refresh mechanism."""
        if not self.testing_mode:
            self.scraper.start_auto_refresh(self.update_table)
        self.refresh_data()  # Initial data load
    
    def on_closing(self):
        """Clean up resources when window is closed."""
        self.scraper.stop_auto_refresh()
        if self.root is not None and not self.testing_mode:
            self.root.destroy()
