#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""数据库初始化测试脚本"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.storage.database import CryptoDatabase
    logger.info("正在测试数据库初始化...")
    db = CryptoDatabase()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.error(f"数据库初始化失败: {str(e)}")
    raise
