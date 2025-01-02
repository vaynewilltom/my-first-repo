import pytest
from unittest.mock import patch, Mock
import asyncio
from datetime import datetime, timedelta
import time

from .market_scraper import MarketScraper
from ..utils.config import UPDATE_INTERVAL

@pytest.fixture
def scraper():
    return MarketScraper()

def test_scraper_initialization(scraper):
    """Test scraper initialization"""
    assert scraper.url == "https://coinmarketcap.com/exchanges/upbit/"
    assert isinstance(scraper.headers, dict)
    assert 'User-Agent' in scraper.headers

def test_get_top_cryptocurrencies_limit(scraper):
    """Test that scraper respects the limit parameter"""
    with patch('requests.Session.get') as mock_get:
        # Mock response with sample HTML
        mock_response = Mock()
        mock_response.text = """
        <div class="cmc-table__table-wrapper-outer">
            <table>
                <tbody>
                    <tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>100M</td></tr>
                    <tr><td></td><td></td><td>Ethereum</td><td>$3,000</td><td>50M</td></tr>
                    <tr><td></td><td></td><td>Dogecoin</td><td>$0.20</td><td>25M</td></tr>
                </tbody>
            </table>
        </div>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test with different limits
        result_5 = scraper.get_top_cryptocurrencies(5)
        assert len(result_5) <= 5

        result_2 = scraper.get_top_cryptocurrencies(2)
        assert len(result_2) <= 2

def test_scraper_data_format(scraper):
    """Test that scraped data contains required fields"""
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.text = """
        <div class="cmc-table__table-wrapper-outer">
            <table>
                <tbody>
                    <tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>100M</td></tr>
                </tbody>
            </table>
        </div>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = scraper.get_top_cryptocurrencies(1)
        assert len(result) == 1
        crypto = result[0]
        assert 'name' in crypto
        assert 'price' in crypto
        assert 'volume' in crypto
        assert isinstance(crypto['name'], str)
        assert isinstance(crypto['price'], str)
        assert isinstance(crypto['volume'], str)

def test_scraper_error_handling(scraper):
    """Test scraper error handling"""
    with patch('requests.Session.get') as mock_get:
        # Test connection error
        mock_get.side_effect = Exception("Connection error")
        result = scraper.get_top_cryptocurrencies()
        assert result == []

        # Test invalid HTML
        mock_response = Mock()
        mock_response.text = "<invalid>html"
        mock_response.status_code = 200
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        result = scraper.get_top_cryptocurrencies()
        assert result == []

@pytest.mark.asyncio
async def test_periodic_scraping():
    """Test periodic scraping functionality"""
    scraper = MarketScraper()
    
    # Mock the scraping function
    with patch.object(scraper, 'get_top_cryptocurrencies') as mock_scrape:
        mock_scrape.return_value = [
            {'name': 'Bitcoin', 'price': '$50,000', 'volume': '100M'}
        ]
        
        # Create a list to store scraping timestamps
        scrape_times = []
        
        async def mock_periodic_scrape():
            for _ in range(3):  # Test 3 intervals
                scrape_times.append(datetime.now())
                result = scraper.get_top_cryptocurrencies()
                assert len(result) > 0
                await asyncio.sleep(UPDATE_INTERVAL / 20)  # Reduced sleep for testing
        
        # Run periodic scraping
        await mock_periodic_scrape()
        
        # Verify timing between scrapes
        for i in range(1, len(scrape_times)):
            time_diff = scrape_times[i] - scrape_times[i-1]
            # Allow for some timing variation
            assert time_diff >= timedelta(seconds=UPDATE_INTERVAL/20 - 0.1)

def test_retry_mechanism(scraper):
    """Test that scraper implements retry mechanism"""
    with patch('requests.Session.get') as mock_get:
        # Simulate temporary failure followed by success
        mock_get.side_effect = [
            Exception("Temporary error"),
            Mock(status_code=200, text="<div class='cmc-table__table-wrapper-outer'><table><tbody><tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>100M</td></tr></tbody></table></div>")
        ]
        
        result = scraper.get_top_cryptocurrencies()
        assert len(result) == 1
        assert result[0]['name'] == 'Bitcoin'

def test_data_consistency(scraper):
    """Test consistency of scraped data format"""
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.text = """
        <div class="cmc-table__table-wrapper-outer">
            <table>
                <tbody>
                    <tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>100M</td></tr>
                    <tr><td></td><td></td><td>Ethereum</td><td>$3,000</td><td>50M</td></tr>
                </tbody>
            </table>
        </div>
        """
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Multiple scrapes should return consistent data format
        for _ in range(3):
            result = scraper.get_top_cryptocurrencies()
            assert len(result) == 2
            for crypto in result:
                assert all(key in crypto for key in ['name', 'price', 'volume'])
                assert all(isinstance(value, str) for value in crypto.values())
