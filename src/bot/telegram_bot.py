from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import asyncio
from typing import Set, Optional
from datetime import datetime

from ..scraper.market_scraper import MarketScraper
from ..utils.config import TELEGRAM_BOT_TOKEN, UPDATE_INTERVAL

logger = logging.getLogger(__name__)

class CryptoMarketBot:
    def __init__(self):
        """Initialize the bot with necessary components"""
        self.scraper = MarketScraper()
        self.active_chats: Set[int] = set()
        self.update_task: Optional[asyncio.Task] = None
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        
    async def start(self):
        """Start the bot"""
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()
        
    async def stop(self):
        """Stop the bot"""
        if self.update_task:
            self.update_task.cancel()
        await self.application.stop()
        
    def format_crypto_data(self, data: list) -> str:
        """Format cryptocurrency data for message"""
        if not data:
            return "No cryptocurrency data available at the moment."
            
        message = "🔄 Top 10 Cryptocurrencies by Volume (Upbit)\n\n"
        for idx, crypto in enumerate(data, 1):
            message += (f"{idx}. {crypto['name']}\n"
                       f"   💰 Price: {crypto['price']}\n"
                       f"   📊 Volume: {crypto['volume']}\n\n")
        message += f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        return message
        
    async def send_updates(self):
        """Send periodic updates to all active chats"""
        while True:
            try:
                if not self.active_chats:
                    await asyncio.sleep(UPDATE_INTERVAL)
                    continue
                    
                crypto_data = self.scraper.get_top_cryptocurrencies()
                message = self.format_crypto_data(crypto_data)
                
                for chat_id in self.active_chats.copy():
                    try:
                        await self.application.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        logger.error(f"Failed to send message to chat {chat_id}: {str(e)}")
                        self.active_chats.remove(chat_id)
                        
            except Exception as e:
                logger.error(f"Error in update loop: {str(e)}")
            finally:
                await asyncio.sleep(UPDATE_INTERVAL)
                
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        chat_id = update.effective_chat.id
        if chat_id not in self.active_chats:
            self.active_chats.add(chat_id)
            if not self.update_task or self.update_task.done():
                self.update_task = asyncio.create_task(self.send_updates())
            await update.message.reply_text(
                "🚀 Welcome to the Crypto Market Bot!\n"
                "You will now receive updates every 5 minutes.\n"
                "Use /stop to stop receiving updates.\n"
                "Use /status to check the bot's status."
            )
        else:
            await update.message.reply_text(
                "You are already receiving updates.\n"
                "Use /stop to stop receiving updates."
            )
            
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stop command"""
        chat_id = update.effective_chat.id
        if chat_id in self.active_chats:
            self.active_chats.remove(chat_id)
            await update.message.reply_text(
                "✋ Updates stopped.\n"
                "Use /start to receive updates again."
            )
        else:
            await update.message.reply_text(
                "You are not currently receiving updates.\n"
                "Use /start to start receiving updates."
            )
            
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /status command"""
        chat_id = update.effective_chat.id
        status = "active" if chat_id in self.active_chats else "inactive"
        total_active = len(self.active_chats)
        
        await update.message.reply_text(
            f"📊 Bot Status\n"
            f"Your updates: {status}\n"
            f"Total active users: {total_active}\n"
            f"Update interval: {UPDATE_INTERVAL} seconds\n\n"
            f"Use /start to start receiving updates\n"
            f"Use /stop to stop receiving updates"
        )
