import os
import sys
import tkinter as tk
import argparse
import logging
from src.gui.main_window import MainWindow
from src.scraper.market_scraper import MarketScraper
from src.storage.data_store import DataStore
from src.visualization.chart import ChartWindow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_data_directory():
    """Create data directory for SQLite database if it doesn't exist."""
    if sys.platform == 'win32':
        data_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CryptoMarketApp')
    else:
        data_dir = os.path.expanduser('~/.local/share/crypto_market_app')
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def main():
    parser = argparse.ArgumentParser(description='Crypto Market App')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    args = parser.parse_args()

    try:
        data_dir = setup_data_directory()
        logger.info(f"Data directory set up at: {data_dir}")

        root = tk.Tk()
        root.title("Crypto Market App")
        
        data_store = DataStore(data_dir=data_dir)
        scraper = MarketScraper()
        app = MainWindow(root, scraper, data_store)
        
        if args.test_mode:
            logger.info("Running in test mode")
            root.after(1000, root.quit)  # Exit after 1 second in test mode
        
        root.mainloop()
        return 0
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
