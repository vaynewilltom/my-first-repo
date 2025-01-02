#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'EOL'
cd ~ && cd ~/repos/my-first-repo && git pull
1. 从CoinMarketCap抓取Upbit交易所数据
2. 解析前20名加密货币信息
3. 定期更新市场数据
4. 监控前10名变化并发送通知
"""

import asyncio
import logging
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
from crypto_market_bot.storage.database import CryptoDatabase
from crypto_market_bot.utils.logger import setup_logger
from crypto_market_bot.utils.config import load_config

logger = setup_logger(__name__)

class MarketScraper:
    def __init__(self, db=None):
        """初始化市场数据抓取器
        
        Args:
            db (CryptoDatabase, optional): 数据库实例. 如果未提供，将创建新实例.
        """
        self.url = 'https://coinmarketcap.com/exchanges/upbit/'
        self.config = load_config()
        self.db = db if db is not None else CryptoDatabase()
        self.last_update_time = None
        self.previous_top_10 = set()
        self.scrape_interval = self.config['SCRAPE_INTERVAL']
        self.running = False
        self.session = None
        self._task = None
        self._lock = asyncio.Lock()

    async def start(self):
        """启动定期抓取任务"""
        async with self._lock:
            if self._task is not None:
                return

            self.running = True
            self.session = aiohttp.ClientSession()
            self._task = asyncio.create_task(self._run())
            return self._task

    async def _run(self):
        """运行定期抓取循环"""
        try:
            while self.running:
                try:
                    await self.scrape_and_process()
                except Exception as e:
                    logger.error(f'抓取过程中出错: {str(e)}')
                    await asyncio.sleep(60)  # 出错后等待1分钟再重试
                else:
                    await asyncio.sleep(self.scrape_interval)
        except Exception as e:
            logger.error(f'定期抓取过程中出错: {str(e)}')
        finally:
            if self.session and not self.session.closed:
                await self.session.close()

    async def stop(self):
        """停止定期抓取"""
        async with self._lock:
            self.running = False
            if self._task:
                try:
                    await self._task
                except Exception as e:
                    logger.error(f'停止抓取任务时出错: {str(e)}')
                finally:
                    self._task = None

    async def close(self):
        """关闭资源"""
        await self.stop()
        if self.session and not self.session.closed:
            await self.session.close()

    async def scrape_market_data(self):
        """抓取市场数据"""
        try:
            logger.info('开始抓取市场数据...')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(self.url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f'请求失败: HTTP {response.status}')
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                crypto_data = []
                
                # 解析前20名加密货币数据
                rows = soup.select('div.sc-beb003d5-3 table tbody tr, table.cmc-table tbody tr')[:20]
                logger.debug(f'找到 {len(rows)} 个交易对数据')
                
                for row in rows:
                    try:
                        # 尝试不同的选择器组合来获取数据
                        name_elem = (
                            row.select_one('td div.name-area p.name') or
                            row.select_one('td:nth-child(3) a') or
                            row.select_one('td:nth-child(2) a')
                        )
                        
                        if not name_elem:
                            continue
                            
                        name = name_elem.get_text().strip()
                        if '/' in name:
                            name = name.split('/')[0].strip()
                            
                        # 解析价格
                        price_elem = (
                            row.select_one('td div.price-area p.price') or
                            row.select_one('td:nth-child(4) span') or
                            row.select_one('td:nth-child(3) span')
                        )
                        if not price_elem:
                            continue
                        price = price_elem.get_text().strip()
                        
                        # 解析交易量百分比
                        volume_elem = (
                            row.select_one('td div.volume-area p.volume') or
                            row.select_one('td:nth-child(7) span') or
                            row.select_one('td:nth-child(6) span')
                        )
                        if not volume_elem:
                            continue
                            
                        volume_text = volume_elem.get_text().strip().replace('%', '')
                        # 提取数字部分
                        volume_text = ''.join(c for c in volume_text if c.isdigit() or c == '.' or c == '-')
                        try:
                            volume = float(volume_text)
                        except ValueError:
                            logger.warning(f'无法解析交易量: {volume_text} - 跳过该条目')
                            continue
                            
                        if volume > 0:  # 只添加有效的数据
                            crypto_data.append({
                                'name': name,
                                'price': price,
                                'volume': volume,
                                'timestamp': datetime.now().isoformat()
                            })
                            logger.debug(f'成功解析: {name} - 价格: {price}, 交易量: {volume}%')
                    except Exception as e:
                        logger.warning(f'解析数据失败: {name if "name" in locals() else "未知"} - {str(e)}')
                        continue
                
                if crypto_data:
                    logger.info(f'成功抓取 {len(crypto_data)} 条加密货币数据')
                else:
                    logger.warning('未找到有效的加密货币数据')
                return crypto_data
                
        except Exception as e:
            logger.error(f'抓取市场数据失败: {str(e)}')
            return None

    async def scrape_and_process(self):
        """抓取并处理市场数据"""
        try:
            crypto_data = await self.scrape_market_data()
            
            if crypto_data:
                # 存储数据
                self.db.save_market_data(crypto_data)
                self.last_update_time = datetime.now()
                logger.info(f'成功保存{len(crypto_data)}条市场数据')
                
                # 检查前10名变化并记录
                current_top_10 = {crypto['name'] for crypto in crypto_data[:10]}
                new_entries = current_top_10 - self.previous_top_10
                
                if new_entries: 
                    logger.info(f'发现新进入前10名的加密货币: {new_entries}')
                    # 这里可以添加通知逻辑
                
                self.previous_top_10 = current_top_10
                return crypto_data
            
            logger.warning('未找到加密货币数据')
            return None
                
        except Exception as e:
            logger.error(f'抓取市场数据失败: {str(e)}')
            return None

if __name__ == '__main__':
    scraper = MarketScraper()
    asyncio.run(scraper.scrape_and_process())
