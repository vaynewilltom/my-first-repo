#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

cd ~ && cd ~/repos/my-first-repo && git pull
1. 初始化并启动Telegram机器人
2. 管理市场数据抓取器
3. 协调各组件工作
4. 处理异常情况
"""

import asyncio
import logging
from datetime import datetime
from utils.logger import setup_logger
from utils.config import load_config
from scraper.market_scraper import MarketScraper
from bot.telegram_bot import CryptoMarketBot

logger = setup_logger(__name__)

class CryptoMarketApp:
    def __init__(self):
        """初始化应用程序"""
        self.config = load_config()
        self.scraper = MarketScraper()
        self.bot = CryptoMarketBot()
        self.running = False
        
    async def start(self):
        """启动应用程序"""
        try:
            logger.info('正在启动加密货币市场机器人...')
            self.running = True
            
            # 启动数据抓取任务
            scraper_task = asyncio.create_task(self.scraper.start())
            
            # 启动Telegram机器人
            bot_task = asyncio.create_task(self.bot.run_async())
            
            # 等待任务完成
            await asyncio.gather(scraper_task, bot_task)
            
        except Exception as e:
            logger.error(f'程序运行出错: {str(e)}')
            await self.close()
            raise
            
    async def close(self):
        """关闭应用程序"""
        if not self.running:
            return
            
        logger.info('正在关闭应用程序...')
        self.running = False
        
        # 结束数据抓取
        await self.scraper.close()
        
        # 关闭Telegram机器人
        if self.bot.application:
            await self.bot.application.close()
            await self.bot.application.cleanup()
            
        logger.info('应用程序已关闭')

def main():
    """主程序入口"""
    app = CryptoMarketApp()
    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info('收到信号，正在退出...')
    except Exception as e:
        logger.error(f'程序异常退出: {str(e)}')
        raise
    finally:
        logger.info('程序已退出')

if __name__ == '__main__':
    main()
