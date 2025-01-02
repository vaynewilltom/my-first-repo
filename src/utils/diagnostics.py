#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
诊断工具
用于检查系统环境和模块导入
"""

import sys
import os
import logging

def check_environment():
    """检查系统环境"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=== Python Path ===")
    for path in sys.path:
        logger.info(path)
    
    logger.info("\n=== Environment Variables ===")
    for key, value in os.environ.items():
        if 'PATH' in key or 'PYTHON' in key:
            logger.info(f"{key}: {value}")
    
    logger.info("\n=== Module Structure ===")
    base_dir = '/opt/crypto_market_bot'
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        logger.info(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for file in files:
            logger.info(f"{subindent}{file}")

if __name__ == '__main__':
    check_environment()
