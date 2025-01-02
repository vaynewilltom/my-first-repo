#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""测试导入模块"""

try:
    from crypto_market_bot.main import main
    from crypto_market_bot.bot.telegram_bot import CryptoMarketBot
    from crypto_market_bot.scraper.market_scraper import MarketScraper
    from crypto_market_bot.storage.database import CryptoDatabase
    from crypto_market_bot.utils.config import load_config
    from crypto_market_bot.utils.logger import setup_logger
    
    print("所有模块导入成功")
except Exception as e:
    print(f"导入错误: {str(e)}")

if __name__ == '__main__':
    pass
