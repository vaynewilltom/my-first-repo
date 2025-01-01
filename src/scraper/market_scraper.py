import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from datetime import datetime
import time
import threading

class MarketScraper:
    def __init__(self):
        self.url = "https://coinmarketcap.com/exchanges/upbit/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self._stop_refresh = False
        self._refresh_thread = None
        self.callback = None
        
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse market data from CoinMarketCap Upbit page."""
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the market data table
            table = soup.find('table')
            if not table:
                raise ValueError("Market data table not found")
            
            # Parse table data
            crypto_data = []
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td'])
                if len(cells) >= 8:  # Ensure we have all required columns
                    try:
                        # Extract and clean volume percentage
                        volume_percent = cells[7].get_text().strip().rstrip('%')
                        volume_percent = float(volume_percent.replace(',', '')) if volume_percent else 0.0
                        
                        # Extract price (remove $ and convert to float)
                        price = cells[3].get_text().strip().lstrip('$')
                        price = float(price.replace(',', '')) if price else 0.0
                        
                        crypto_data.append({
                            'name': cells[1].get_text().strip(),
                            'price': price,
                            'volume_percent': volume_percent,
                            'timestamp': datetime.now()
                        })
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing row: {e}")
                        continue
            
            # Sort by volume percentage in descending order and get top 10
            crypto_data.sort(key=lambda x: x['volume_percent'], reverse=True)
            return crypto_data[:10]
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
    
    def start_auto_refresh(self, callback=None, testing=False):
        """Start auto-refresh thread that updates data every 5 minutes."""
        self.callback = callback
        self._stop_refresh = False
        
        if testing:
            # In testing mode, just run one iteration
            self._auto_refresh_task(testing=True)
        else:
            self._refresh_thread = threading.Thread(target=lambda: self._auto_refresh_task(testing=False))
            self._refresh_thread.daemon = True
            self._refresh_thread.start()
    
    def stop_auto_refresh(self):
        """Stop the auto-refresh thread."""
        self._stop_refresh = True
        if self._refresh_thread:
            self._refresh_thread.join()
    
    def _auto_refresh_task(self, testing=False):
        """Background task for auto-refreshing data."""
        while not self._stop_refresh:
            data = self.fetch_data()
            if self.callback:
                self.callback(data)
            time.sleep(300)  # Wait for 5 minutes
            if testing:
                break  # Exit after one iteration in testing mode
