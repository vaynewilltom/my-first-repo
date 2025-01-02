from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
import asyncio
import plotly.graph_objects as go
from typing import Set, Optional, Dict, List
from datetime import datetime, timedelta
import tempfile
import os

from ..scraper.market_scraper import MarketScraper
from ..storage.database import CryptoDatabase
from ..utils.config import TELEGRAM_BOT_TOKEN, UPDATE_INTERVAL

logger = logging.getLogger(__name__)

class CryptoMarketBot:
    def __init__(self):
        """Initialize the bot with necessary components"""
        self.scraper = MarketScraper()
        self.db = CryptoDatabase()
        self.active_chats: Set[int] = set()
        self.update_task: Optional[asyncio.Task] = None
        self.last_update_time: Optional[datetime] = None
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stop", self.stop_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("gettop10", self.gettop10_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_chart_callback, pattern=r'^chart_.*$'))
        
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
                       f"   💰 Price: ${crypto['price']:,.2f}\n"
                       f"   📊 Volume: {crypto['volume_percentage']:.1f}%\n\n")
        message += f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        return message
        
    async def gettop10_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /gettop10 command"""
        try:
            # Get top 20 and slice to get top 10
            crypto_data = self.scraper.get_top_cryptocurrencies(20)[:10]
            if not crypto_data:
                await update.message.reply_text(
                    "Unable to fetch cryptocurrency data at the moment. Please try again later."
                )
                return

            # Create inline keyboard with chart buttons
            keyboard = []
            for crypto in crypto_data:
                button = InlineKeyboardButton(
                    f"📈 {crypto['name']} Chart",
                    callback_data=f"chart_{crypto['name']}"
                )
                keyboard.append([button])

            reply_markup = InlineKeyboardMarkup(keyboard)
            message = self.format_crypto_data(crypto_data)
            
            await update.message.reply_text(
                message,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error in gettop10 command: {str(e)}")
            await update.message.reply_text(
                "Sorry, there was an error processing your request. Please try again later."
            )
            
    async def handle_chart_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle chart button callbacks"""
        query = update.callback_query
        try:
            # Extract cryptocurrency name from callback data
            crypto_name = query.data.split('_')[1]
            
            # Get historical data for the last 24 hours
            historical_data = self.db.get_crypto_history(
                crypto_name,
                datetime.now() - timedelta(hours=24)
            )
            
            if not historical_data:
                await query.answer("No historical data available for this cryptocurrency.")
                return
                
            # Create the chart
            fig = go.Figure()
            timestamps = [entry['timestamp'] for entry in historical_data]
            volumes = [entry['volume_percentage'] for entry in historical_data]
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=volumes,
                mode='lines+markers',
                name=f'{crypto_name} Volume %'
            ))
            
            fig.update_layout(
                title=f'{crypto_name} 24h Trading Volume Percentage',
                xaxis_title='Time',
                yaxis_title='Volume %',
                template='plotly_dark'
            )
            
            # Save chart to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                fig.write_image(tmp.name)
                # Send the chart
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=open(tmp.name, 'rb'),
                    caption=f"24-hour trading volume trend for {crypto_name}"
                )
                # Clean up
                tmp.close()
                os.unlink(tmp.name)
                
            await query.answer()
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            await query.answer("Error generating chart. Please try again later.")
        
    async def send_updates(self):
        """Send periodic updates to all active chats"""
        while True:
            try:
                if not self.active_chats:
                    await asyncio.sleep(UPDATE_INTERVAL)
                    continue
                    
                crypto_data = self.scraper.get_top_cryptocurrencies()
                self.last_update_time = datetime.now()
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
                "Available commands:\n"
                "• /gettop10 - Get current top 10 cryptocurrencies\n"
                "• /stop - Stop receiving updates\n"
                "• /status - Check bot status"
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
        
        last_update = "Never" if self.last_update_time is None else \
                  self.last_update_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        await update.message.reply_text(
            f"📊 Bot Status\n"
            f"Your updates: {status}\n"
            f"Total active users: {total_active}\n"
            f"Update interval: {UPDATE_INTERVAL} seconds\n"
            f"Last update: {last_update}\n\n"
            f"Use /start to start receiving updates\n"
            f"Use /stop to stop receiving updates"
        )
