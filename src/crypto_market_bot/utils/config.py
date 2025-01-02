#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
功能：
1. 加载环境变量
2. 提供全局配置访问
3. 管理应用程序设置
"""

import os
from dotenv import load_dotenv

def load_config():
    """加载配置信息"""
    load_dotenv()
    
    config = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'DB_PATH': os.path.expanduser(os.getenv('DB_PATH', '~/.crypto_market_bot/data/market_data.db')),
        'LOG_PATH': os.path.expanduser(os.getenv('LOG_PATH', '~/.crypto_market_bot/logs/bot.log')),
        'SCRAPE_INTERVAL': int(os.getenv('SCRAPE_INTERVAL', '300')),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
        'UPDATE_INTERVAL': 300,  # 5 minutes in seconds
        'MAX_RETRIES': 3,
        'RETRY_DELAY': 60  # 1 minute in seconds
    }
    
    if not config['TELEGRAM_BOT_TOKEN']:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
    
    return config
