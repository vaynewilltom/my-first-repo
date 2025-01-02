#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'EOL''EOL'
cd ~ && cd ~/repos/my-first-repo && git pull
1. 创建和管理SQLite数据库
2. 存储加密货币市场数据
3. 提供历史数据查询接口
4. 支持数据缓存和性能优化
"""

import sqlite3
import os
from datetime import datetime, timedelta
from ..utils.logger import setup_logger
from ..utils.config import load_config

logger = setup_logger(__name__)

class CryptoDatabase:
    def __init__(self):
        """初始化数据库连接并创建必要的表"""
        config = load_config()
        self.db_path = config['DB_PATH']
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """创建数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 创建市场数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price TEXT NOT NULL,
                        volume REAL NOT NULL,
                        timestamp DATETIME NOT NULL
                    )
                ''')
                # 创建索引以优化查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_name_timestamp ON market_data(name, timestamp)')
                conn.commit()
                logger.info('数据库初始化成功')
        except Exception as e:
            logger.error(f'数据库初始化失败: {str(e)}')
            raise

    def save_market_data(self, data_list):
        """保存市场数据到数据库
        
        Args:
            data_list: 包含市场数据的字典列表
                [{'name': str, 'price': str, 'volume': float, 'timestamp': datetime}, ...]
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    'INSERT INTO market_data (name, price, volume, timestamp) VALUES (?, ?, ?, ?)',
                    [(d['name'], d['price'], d['volume'], d['timestamp']) for d in data_list]
                )
                conn.commit()
                logger.info(f'成功保存{len(data_list)}条市场数据')
        except Exception as e:
            logger.error(f'保存市场数据失败: {str(e)}')
            raise

    def get_latest_data(self, limit=10):
        """获取最新的市场数据
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            包含最新市场数据的字典列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT name, price, volume, timestamp
                    FROM market_data
                    WHERE timestamp = (
                        SELECT MAX(timestamp) FROM market_data
                    )
                    ORDER BY volume DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                return [
                    {
                        'name': row[0],
                        'price': row[1],
                        'volume': row[2],
                        'timestamp': row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f'获取最新数据失败: {str(e)}')
            return []

    def get_history(self, crypto_name, hours=24):
        """获取指定加密货币的历史数据
        
        Args:
            crypto_name: 加密货币名称
            hours: 历史数据时间范围（小时）
            
        Returns:
            包含历史数据的字典列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                time_threshold = datetime.now() - timedelta(hours=hours)
                cursor.execute('''
                    SELECT timestamp, volume
                    FROM market_data
                    WHERE name = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (crypto_name, time_threshold))
                rows = cursor.fetchall()
                return [{'timestamp': row[0], 'volume': row[1]} for row in rows]
        except Exception as e:
            logger.error(f'获取历史数据失败: {str(e)}')
            return []

    def cleanup_old_data(self, days=7):
        """清理旧数据以优化数据库性能
        
        Args:
            days: 保留数据的天数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                time_threshold = datetime.now() - timedelta(days=days)
                cursor.execute('DELETE FROM market_data WHERE timestamp < ?', (time_threshold,))
                conn.commit()
                logger.info(f'成功清理{cursor.rowcount}条旧数据')
        except Exception as e:
            logger.error(f'清理旧数据失败: {str(e)}')
            raise

if __name__ == '__main__':
    db = CryptoDatabase()
    logger.info('数据库模块测试成功')
