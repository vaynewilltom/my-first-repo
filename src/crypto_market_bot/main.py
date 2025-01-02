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
import signal
from datetime import datetime
from telegram import Update
from telegram.ext import Application
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .utils.logger import setup_logger
from .utils.config import load_config
from .scraper.market_scraper import MarketScraper
from .bot.telegram_bot import CryptoMarketBot
from .storage.database import CryptoDatabase

logger = setup_logger(__name__)

class CryptoMarketApp:
    def __init__(self):
        """初始化应用程序"""
        self.config = load_config()
        self.running = False
        self.db = CryptoDatabase()  # Database will load config internally
        self.scraper = MarketScraper(self.db)
        self.bot = CryptoMarketBot(
            token=self.config['TELEGRAM_BOT_TOKEN'],
            scraper=self.scraper,
            db=self.db
        )
        
    async def start(self):
        """启动应用程序"""
        try: 
            logger.info('正在启动加密货币市场机器人...')
            self.running = True
            
            # 初始化数据库
            self.db.init_db()
            logger.info('数据库初始化成功')
            
            # 初始化机器人和数据抓取器
            self.stop_event = asyncio.Event()
            
            # 设置信号处理
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.handle_signal(s)))
            
            # 启动数据抓取任务
            scraper_task = asyncio.create_task(self.scraper.start())
            
            # 初始化并启动机器人
            await self.bot.initialize()
            bot_task = asyncio.create_task(self.bot.start())
            
            logger.info('Telegram机器人和数据抓取任务已启动')
            
            # 等待任务完成或停止信号
            tasks = [scraper_task, bot_task]
            stop_task = asyncio.create_task(self.stop_event.wait())
            tasks.append(stop_task)
            
            try:
                done, pending = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # 检查是否有任务异常退出
                for task in done:
                    try:
                        await task
                    except Exception as e:
                        logger.error(f'任务执行出错: {str(e)}')
                        raise
                        
            except asyncio.CancelledError:
                logger.info('收到取消信号，正在关闭任务...')
            except Exception as e:
                logger.error(f'任务执行出错: {str(e)}')
                raise
            finally:
                # 取消所有未完成的任务
                for task in pending:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
            # 取消剩余任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
        except asyncio.CancelledError:
            logger.info('收到取消信号，正在关闭任务...')
        except Exception as e:
            logger.error(f'程序运行出错: {str(e)}')
            raise
        finally:
            self.running = False
            await self.close()
            logger.info('程序已停止运行')
            
    async def close(self):
        """关闭应用程序"""
        if not self.running:
            return
            
        logger.info('正在关闭应用程序...')
        self.running = False
        
        
        # 结束数据抓取
        try:
            await self.scraper.close()
        except Exception as e:
            logger.error(f'关闭数据抓取器时出错: {str(e)}')
        
        # 关闭Telegram机器人
        try:
            if self.bot.application:
                await self.bot.stop()
        except Exception as e:
            logger.error(f'关闭Telegram机器人时出错: {str(e)}')
            
        logger.info('应用程序已关闭')
        
    async def handle_signal(self, sig):
        """处理系统信号"""
        logger.info(f'收到信号 {sig.name}，准备关闭...')
        if hasattr(self, 'stop_event'):
            self.stop_event.set()

def main():
    """主程序入口"""
    app = CryptoMarketApp()
    try:
        # 设置更详细的日志级别
        logging.getLogger('crypto_market_bot').setLevel(logging.DEBUG)
        logger.debug('开始初始化应用程序...')
        
        # 使用asyncio.run来管理事件循环
        asyncio.run(app.start())
    except KeyboardInterrupt:
        logger.info('收到信号，正在退出...')
    except Exception as e:
        logger.error(f'程序异常退出: {str(e)}')
        logger.exception('详细错误信息:')
        raise
    finally:
        logger.info('程序已退出')

if __name__ == '__main__':
    main()
