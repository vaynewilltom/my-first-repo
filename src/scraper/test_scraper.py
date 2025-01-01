import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

def inspect_webpage():
    """Inspect the CoinMarketCap Upbit page structure."""
    url = 'https://coinmarketcap.com/exchanges/upbit/'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        print(f'Status Code: {response.status_code}')
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print('\nPage Title:', soup.title.string if soup.title else 'No title found')
        
        # Try to find the market data table
        tables = soup.find_all('table')
        print(f'\nNumber of tables found: {len(tables)}')
        
        # Look for relevant table headers
        headers = soup.find_all(['th', 'td'])
        print('\nTable headers/cells found:')
        for header in headers[:20]:  # Print first 20 headers/cells
            print(f'- {header.get_text().strip()}')
            
    except Exception as e:
        print(f'Error occurred: {e}')

if __name__ == '__main__':
    inspect_webpage()
