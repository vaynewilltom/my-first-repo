import os
import sys

def init_data_dir():
    """Initialize data directory for SQLite database."""
    if sys.platform == 'win32':
        data_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'CryptoMarketApp')
    else:
        data_dir = os.path.expanduser('~/.local/share/crypto_market_app')
    
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

# Create data directory at startup
init_data_dir()
