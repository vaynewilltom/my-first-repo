#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
'EOL'
cd ~ && cd ~/repos/my-first-repo && git pull
1. 配置日志格式和级别
2. 提供统一的日志接口
3. 支持文件和控制台输出
"""

import logging
import os
from datetime import datetime

def setup_logger(name=None):
    """配置并返回logger实例"""
    from .config import load_config
    config = load_config()
    log_path = config.get('LOG_PATH', '/var/log/crypto_market_bot/bot.log')
    
    # 创建日志目录
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name or __name__)
    if logger.handlers:  # 避免重复配置
        return logger
        
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.INFO)
    
    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

if __name__ == '__main__':
    logger = setup_logger(__name__)
    logger.info('日志模块测试成功')
