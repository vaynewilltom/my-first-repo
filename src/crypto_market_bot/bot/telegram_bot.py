#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram机器人模块
cd ~ && cd ~/repos/my-first-repo && git pull
1. 处理用户命令
2. 显示加密货币数据
3. 生成交易量趋势图
4. 发送自动通知
"""

import asyncio
import logging
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sys
import os

# 设置北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ..scraper.market_scraper import MarketScraper
from ..storage.database import CryptoDatabase
from ..utils.logger import setup_logger
from ..utils.config import load_config

logger = setup_logger(__name__)

class CryptoMarketBot:
    def __init__(self, token=None, scraper=None, db=None):
        """初始化Telegram机器人"""
        self.config = load_config()
        self.token = token or self.config['TELEGRAM_BOT_TOKEN']
        self.scraper = scraper or MarketScraper()
        self.db = db or CryptoDatabase()
        self.application = None
        self._running = False
        self.previous_ranks = {}
        
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/start命令"""
        await update.message.reply_text(
            '欢迎使用加密货币市场机器人！\n'
            '使用以下命令：\n'
            '/gettop10 - 获取前10名加密货币\n'
            '/status - 查看机器人状态'
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/status命令"""
        last_update = self.scraper.last_update_time
        status_text = f'机器人状态：运行中\n最后更新时间：{last_update}'
        await update.message.reply_text(status_text)

    async def get_top_10(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/gettop10命令"""
        # 获取前20名数据以检测新进入前10的币种
        crypto_data = self.db.get_latest_data(limit=20)
        if not crypto_data:
            await update.message.reply_text('暂无数据，请稍后再试。')
            return

        # 获取当前排名
        current_ranks = {crypto["name"]: i+1 for i, crypto in enumerate(crypto_data)}
        
        keyboard = []
        message = '前10名加密货币：\n\n'
        for i, crypto in enumerate(crypto_data[:10], 1):
            name = crypto["name"]
            # 检查是否是新进入前10的币种（之前排名在11-20之间）
            prev_rank = self.previous_ranks.get(name, 0)
            if 10 < prev_rank <= 20:
                # 标红显示新进入前10的币种
                name_display = f'<font color="red">{name}</font>'
            else:
                name_display = name
            message += f'{i}. {name_display} - {crypto["volume"]}%\n'
            keyboard.append([InlineKeyboardButton(
                f'查看{name}走势',
                callback_data=f'chart_{name}'
            )])
            
        # 更新排名记录
        self.previous_ranks = current_ranks
        
        # 添加帮助按钮
        keyboard.append([InlineKeyboardButton("帮助", callback_data="help_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith('chart_'):
            crypto_name = query.data[6:]
            chart_data = self.db.get_history(crypto_name)
            if not chart_data:
                await query.message.reply_text(f'无法获取{crypto_name}的历史数据。')
                return
            
            # 限制显示最新的30条记录
            chart_data = sorted(chart_data, key=lambda x: x['timestamp'], reverse=True)[:30]
            # 按时间正序显示
            chart_data = sorted(chart_data, key=lambda x: x['timestamp'])
            
            chart_text = '\n'.join([
                f'时间: {data["timestamp"]} | 占比: {data["volume"]}% | 排名: {data["rank"] or "未知"}'
                for data in chart_data
            ])
            await query.message.reply_text(
                f'{crypto_name}的交易量走势（最近30条记录）：\n\n{chart_text}',
                parse_mode='HTML'
            )
        elif query.data == "help_menu":
            help_text = (
                "<b>可用命令：</b>\n\n"
                "/start - 启动机器人\n"
                "/gettop10 - 查看前10名加密货币\n"
                "/status - 查看机器人运行状态\n\n"
                "<b>功能说明：</b>\n"
                "• 每5分钟自动更新数据\n"
                "• 红色标记表示新进入前10的币种\n"
                "• 点击币种可查看历史走势\n"
                "• 历史数据显示最近30条记录"
            )
            await query.message.reply_text(help_text, parse_mode='HTML')

    async def initialize(self):
        """初始化机器人"""
        if self.application:
            return
            
        try:
            # 构建应用程序
            self.application = (
                Application.builder()
                .token(self.token)
                .concurrent_updates(True)
                .build()
            )
            
            # 添加命令处理器
            self.application.add_handler(CommandHandler('start', self.cmd_start))
            self.application.add_handler(CommandHandler('status', self.status))
            self.application.add_handler(CommandHandler('gettop10', self.get_top_10))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # 设置定期抓取任务
            job_queue = self.application.job_queue
            job_queue.run_repeating(
                self.scrape_job,
                interval=300,  # 5分钟
                first=1,
                name='market_scraper'
            )
            
            # 初始化应用程序
            await self.application.initialize()
            await self.application.start()
            
            logger.info('Telegram机器人初始化成功')
            
        except Exception as e:
            logger.error(f'初始化Telegram机器人失败: {str(e)}')
            self.application = None
            raise

    async def scrape_job(self, context):
        """定期抓取任务"""
        try:
            await self.scraper.scrape_and_process()
        except Exception as e:
            logger.error(f'抓取任务出错: {str(e)}')

    async def start(self):
        """启动机器人"""
        try:
            logger.debug('开始启动Telegram机器人...')
            if not self.application:
                logger.debug('初始化Telegram应用程序...')
                await self.initialize()
            
            if not self.application:
                raise RuntimeError("无法初始化Telegram机器人")
            
            logger.info('开始运行Telegram机器人...')
            self._running = True
            
            # 等待停止信号
            while self._running:
                await asyncio.sleep(1)
                
        except Exception as e: 
            logger.error(f'机器人运行出错: {str(e)}')
            logger.exception('详细错误信息:')
            await self.stop()
            raise

    async def stop(self):
        """停止机器人"""
        try:
            self._running = False
            if self.application:
                if hasattr(self.application, 'updater') and self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self.application = None
                logger.info('Telegram机器人已关闭')
        except Exception as e:
            logger.error(f'关闭机器人时出错: {str(e)}')

if __name__ == '__main__':
    bot = CryptoMarketBot()
    asyncio.run(bot.start())
