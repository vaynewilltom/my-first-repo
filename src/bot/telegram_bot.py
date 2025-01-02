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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from ..scraper.market_scraper import MarketScraper
from ..storage.database import CryptoDatabase
from ..utils.logger import setup_logger
from ..utils.config import load_config

logger = setup_logger(__name__)

class CryptoMarketBot:
    def __init__(self):
        """初始化Telegram机器人"""
        self.config = load_config()
        self.token = self.config['TELEGRAM_BOT_TOKEN']
        self.scraper = MarketScraper()
        self.db = CryptoDatabase()
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        crypto_data = self.db.get_latest_data(limit=10)
        if not crypto_data:
            await update.message.reply_text('暂无数据，请稍后再试。')
            return

        keyboard = []
        message = '前10名加密货币：\n\n'
        for i, crypto in enumerate(crypto_data, 1):
            message += f'{i}. {crypto["name"]}\n'
            message += f'   价格: {crypto["price"]}\n'
            message += f'   交易量: {crypto["volume"]}%\n\n'
            keyboard.append([InlineKeyboardButton(
                f'查看{crypto["name"]}走势',
                callback_data=f'chart_{crypto["name"]}'
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup)

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
                
            chart_text = '\n'.join([f'{data["timestamp"]}: {data["volume"]}%' for data in chart_data])
            await query.message.reply_text(f'{crypto_name}的24小时交易量走势：\n{chart_text}')

    async def run_async(self):
        """异步运行机器人"""
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('status', self.status))
        self.application.add_handler(CommandHandler('gettop10', self.get_top_10))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()

if __name__ == '__main__':
    bot = CryptoMarketBot()
    asyncio.run(bot.run_async())
