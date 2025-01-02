#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境检查脚本
功能：
1. 检查Python环境
2. 验证已安装的包
3. 检查系统配置
4. 验证日志文件权限
"""

import sys
import os
import pkg_resources
import logging
from pathlib import Path

def check_environment():
    """检查运行环境并输出状态"""
    print("=== Python环境检查 ===")
    print(f"Python版本: {sys.version}")
    print("\nPython路径:")
    for path in sys.path:
        print(f"  {path}")
        
    print("\n=== 已安装的包 ===")
    required_packages = [
        'python-telegram-bot',
        'requests',
        'beautifulsoup4',
        'matplotlib',
        'python-dotenv',
        'aiohttp'
    ]
    
    for package in required_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"{package}: {version}")
        except pkg_resources.DistributionNotFound:
            print(f"{package}: 未安装")
            
    print("\n=== 系统配置检查 ===")
    paths_to_check = [
        '/opt/crypto_market_bot',
        '/opt/crypto_market_bot/data',
        '/var/log/crypto_market_bot',
        '/opt/crypto_market_bot/.env'
    ]
    
    for path in paths_to_check:
        p = Path(path)
        if p.exists():
            perms = oct(p.stat().st_mode)[-3:]
            owner = p.owner()
            group = p.group()
            print(f"{path}: 存在 (权限: {perms}, 所有者: {owner}:{group})")
        else:
            print(f"{path}: 不存在")

if __name__ == '__main__':
    check_environment()
