import pytest
from unittest.mock import patch, Mock, MagicMock
import asyncio
from datetime import datetime, timedelta
import time

from .market_scraper import MarketScraper
from ..storage.database import CryptoDatabase
from ..utils.config import UPDATE_INTERVAL

@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = Mock(spec=CryptoDatabase)
    db.get_last_update_time.return_value = datetime.now()
    return db

@pytest.fixture
def scraper(mock_db):
    """Create a scraper with mock database."""
    return MarketScraper(mock_db)

def test_scraper_initialization(scraper, mock_db):
    """Test scraper initialization"""
    assert scraper.url == "https://coinmarketcap.com/exchanges/upbit/"
    assert isinstance(scraper.headers, dict)
    assert 'User-Agent' in scraper.headers
    assert scraper.db == mock_db
    assert not scraper.is_running

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
    """Test that scraped data contains required fields with correct types"""
    with patch('requests.Session.get') as mock_get:
        mock_response = Mock()
        mock_response.text = """
        <div class="cmc-table__table-wrapper-outer">
            <table>
                <tbody>
                    <tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>25.5%</td></tr>
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
        assert 'rank' in crypto
        assert 'price' in crypto
        assert 'volume_percentage' in crypto
        assert isinstance(crypto['name'], str)
        assert isinstance(crypto['rank'], int)
        assert isinstance(crypto['price'], float)
        assert isinstance(crypto['volume_percentage'], float)
        assert crypto['price'] == 50000.0
        assert crypto['volume_percentage'] == 25.5

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

def test_periodic_updates(scraper, mock_db):
    """Test periodic update functionality"""
    mock_data = [
        {
            'name': 'Bitcoin',
            'rank': 1,
            'price': 50000.0,
            'volume_percentage': 25.5
        }
    ]
    
    with patch.object(scraper, 'get_top_cryptocurrencies', return_value=mock_data):
        # Start periodic updates
        scraper.start_periodic_updates(interval_minutes=1)
        assert scraper.is_running
        assert scraper.scheduler.running
        
        # Wait briefly to allow one update
        time.sleep(2)
        
        # Verify database interactions
        mock_db.insert_crypto_data.assert_called_with(mock_data)
        mock_db.cleanup_old_data.assert_called_with(hours=48)
        
        # Stop updates
        scraper.stop_periodic_updates()
        assert not scraper.is_running
        assert not scraper.scheduler.running

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
                    <tr><td></td><td></td><td>Bitcoin</td><td>$50,000</td><td>25.5%</td></tr>
                    <tr><td></td><td></td><td>Ethereum</td><td>$3,000</td><td>15.3%</td></tr>
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
                assert all(key in crypto for key in ['name', 'rank', 'price', 'volume_percentage'])
                assert isinstance(crypto['name'], str)
                assert isinstance(crypto['rank'], int)
                assert isinstance(crypto['price'], float)
                assert isinstance(crypto['volume_percentage'], float)

def test_update_market_data(scraper, mock_db):
    """Test market data update process"""
    mock_data = [
        {
            'name': 'Bitcoin',
            'rank': 1,
            'price': 50000.0,
            'volume_percentage': 25.5
        }
    ]
    
    with patch.object(scraper, 'get_top_cryptocurrencies', return_value=mock_data):
        success = scraper.update_market_data()
        assert success
        mock_db.insert_crypto_data.assert_called_once_with(mock_data)
        mock_db.cleanup_old_data.assert_called_once_with(hours=48)

def test_get_last_update_time(scraper, mock_db):
    """Test getting last update timestamp"""
    expected_time = datetime.now()
    mock_db.get_last_update_time.return_value = expected_time
    
    result = scraper.get_last_update_time()
    assert result == expected_time
    mock_db.get_last_update_time.assert_called_once()

def test_detect_new_entries(scraper, mock_db):
    """Test detection of new entries in top 10."""
    # Mock current data
    current_data = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 50000.0, 'volume_percentage': 25.5},
        {'name': 'NewCoin', 'rank': 2, 'price': 1000.0, 'volume_percentage': 20.0},
    ]
    
    # Mock previous data
    mock_db.get_previous_top_n.return_value = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 49000.0, 'volume_percentage': 24.5},
        {'name': 'OldCoin', 'rank': 2, 'price': 500.0, 'volume_percentage': 19.0},
    ]
    
    # Test detection
    new_entries = scraper.detect_new_entries(current_data, n=2)
    assert len(new_entries) == 1
    assert new_entries[0]['name'] == 'NewCoin'
    mock_db.get_previous_top_n.assert_called_once_with(2)

def test_format_new_entry_message(scraper):
    """Test formatting of new entry notification message."""
    entry = {
        'name': 'TestCoin',
        'rank': 5,
        'price': 1234.56,
        'volume_percentage': 15.7
    }
    
    message = scraper.format_new_entry_message(entry)
    assert '🚨 New Top 10 Entry!' in message
    assert 'TestCoin has entered the top 10!' in message
    assert 'Current Rank: #5' in message
    assert 'Price: $1,234.56' in message
    assert 'Volume: 15.7%' in message

def test_notification_callback(scraper, mock_db):
    """Test notification callback functionality."""
    # Create mock callback
    mock_callback = Mock()
    scraper.set_notification_callback(mock_callback)
    
    # Mock current and previous data
    current_data = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 50000.0, 'volume_percentage': 25.5},
        {'name': 'NewCoin', 'rank': 2, 'price': 1000.0, 'volume_percentage': 20.0},
    ]
    
    mock_db.get_previous_top_n.return_value = [
        {'name': 'Bitcoin', 'rank': 1, 'price': 49000.0, 'volume_percentage': 24.5},
        {'name': 'OldCoin', 'rank': 2, 'price': 500.0, 'volume_percentage': 19.0},
    ]
    
    # Mock get_top_cryptocurrencies
    with patch.object(scraper, 'get_top_cryptocurrencies', return_value=current_data):
        # Update market data
        success = scraper.update_market_data()
        assert success
        
        # Verify callback was called with correct message
        mock_callback.assert_called_once()
        message = mock_callback.call_args[0][0]
        assert 'NewCoin has entered the top 10!' in message
