from src.scraper.market_scraper import MarketScraper
import time

def test_scraper():
    """Test the MarketScraper implementation."""
    scraper = MarketScraper()
    
    print("Testing initial data fetch...")
    data = scraper.fetch_data()
    
    if not data:
        print("Error: No data returned")
        return
        
    print(f"\nSuccessfully fetched {len(data)} cryptocurrencies")
    print("\nTop 3 cryptocurrencies by volume percentage:")
    for i, crypto in enumerate(data[:3], 1):
        print(f"{i}. {crypto['name']}")
        print(f"   Price: ${crypto['price']:.2f}")
        print(f"   Volume %: {crypto['volume_percent']:.2f}%")
    
    print("\nTesting auto-refresh functionality...")
    def refresh_callback(new_data):
        print(f"\nReceived new data at {time.strftime('%H:%M:%S')}")
        print(f"Number of cryptocurrencies: {len(new_data)}")
    
    scraper.start_auto_refresh(refresh_callback)
    print("Auto-refresh started. Waiting for 10 seconds to test callback...")
    time.sleep(10)
    
    print("\nStopping auto-refresh...")
    scraper.stop_auto_refresh()
    print("Test completed.")

if __name__ == '__main__':
    test_scraper()
