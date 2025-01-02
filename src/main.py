import asyncio
import signal
import sys
import logging
from bot.telegram_bot import CryptoMarketBot
from utils.logger import setup_logger

def handle_shutdown(bot: CryptoMarketBot, signum, frame):
    """Handle shutdown signals gracefully"""
    logging.info("Received shutdown signal. Stopping bot...")
    asyncio.create_task(bot.stop())
    sys.exit(0)

async def main():
    """Main entry point for the Crypto Market Bot"""
    # Set up logging
    setup_logger()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize and start the bot
        logger.info("Starting Crypto Market Bot...")
        bot = CryptoMarketBot()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: handle_shutdown(bot, s, f))
        signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown(bot, s, f))
        
        # Start the bot
        await bot.start()
        
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
