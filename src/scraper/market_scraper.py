import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from ..storage.database import CryptoDatabase

logger = logging.getLogger(__name__)

class MarketScraper:
    def __init__(self, db: CryptoDatabase):
        """Initialize the market scraper with database connection.
        
        Args:
            db: Database instance for storing scraped data
        """
        self.db = db
        self.url = "https://coinmarketcap.com/exchanges/upbit/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = self._create_session()
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_top_cryptocurrencies(self, limit: int = 20) -> List[Dict]:
        """
        Scrape top cryptocurrencies from CoinMarketCap's Upbit page
        
        Args:
            limit: Number of top cryptocurrencies to return (default: 20)
            
        Returns:
            List of dictionaries containing cryptocurrency data with fields:
            - name: str
            - rank: int
            - price: float
            - volume_percentage: float
        """
        try:
            response = self.session.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            crypto_data = []
            
            # Try different table selectors
            table = None
            selectors = [
                'div.cmc-table__table-wrapper-outer table',
                'div[class*="table"] table',
                'table'
            ]
            
            for selector in selectors:
                table = soup.select_one(selector)
                if table:
                    break
                    
            if not table:
                logger.error("Could not find cryptocurrency table")
                return []
            
            # Find all rows (both in thead and tbody)
            rows = table.select('tr')
            if not rows: 
                logger.error("No rows found in table")
                return []
                
            # Skip header row(s)
            data_rows = rows[1:limit+1]
            
            for row in data_rows:
                try:
                    # Find all columns using CSS selectors
                    cols = row.select('td')
                    if len(cols) >= 5:
                        name = cols[2].get_text(strip=True)
                        price = cols[3].get_text(strip=True)
                        volume = cols[4].get_text(strip=True)
                        
                        if name and price and volume:
                            try:
                                # Clean and convert price (remove $ and commas)
                                price_value = float(price.replace('$', '').replace(',', ''))
                                
                                # Clean and convert volume percentage (remove % and commas)
                                volume_percentage = float(volume.replace('%', '').replace(',', ''))
                                
                                crypto_data.append({
                                    'name': name,
                                    'rank': len(crypto_data) + 1,  # 1-based ranking
                                    'price': price_value,
                                    'volume_percentage': volume_percentage
                                })
                            except ValueError as ve:
                                logger.warning(f"Error converting values for {name}: {ve}")
                                continue
                except Exception as e:
                    logger.warning(f"Error parsing row: {str(e)}")
                    continue
            
            if not crypto_data:
                logger.error("No cryptocurrency data could be extracted")
            
            return crypto_data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching data: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing data: {str(e)}")
            return []

    def update_market_data(self) -> bool:
        """Scrape and store market data in the database.
        
        Returns:
            bool: True if data was successfully updated, False otherwise
        """
        try:
            crypto_data = self.get_top_cryptocurrencies()
            if crypto_data:
                self.db.insert_crypto_data(crypto_data)
                self.db.cleanup_old_data(hours=48)  # Keep 48 hours of historical data
                logger.info("Market data updated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
            return False

    def start_periodic_updates(self, interval_minutes: int = 5) -> None:
        """Start periodic market data updates.
        
        Args:
            interval_minutes: Update interval in minutes (default: 5)
        """
        if not self.is_running:
            self.scheduler.add_job(
                self.update_market_data,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='market_update',
                name='Periodic Market Update',
                replace_existing=True
            )
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Started periodic updates every {interval_minutes} minutes")

    def stop_periodic_updates(self) -> None:
        """Stop periodic market data updates."""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Stopped periodic updates")

    def get_last_update_time(self) -> Optional[datetime]:
        """Get the timestamp of the last successful update."""
        return self.db.get_last_update_time()
