import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class MarketScraper:
    def __init__(self):
        self.url = "https://coinmarketcap.com/exchanges/upbit/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = self._create_session()

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

    def get_top_cryptocurrencies(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Scrape top cryptocurrencies from CoinMarketCap's Upbit page
        
        Args:
            limit: Number of top cryptocurrencies to return
            
        Returns:
            List of dictionaries containing cryptocurrency data
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
                            crypto_data.append({
                                'name': name,
                                'price': price,
                                'volume': volume
                            })
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
