import logging
import sys

def setup_logger():
    """Configure logging for the application"""
    # Ensure log directory exists with correct permissions
    log_dir = "/var/log/crypto_market_bot"
    try:
        import os
        os.makedirs(log_dir, mode=0o755, exist_ok=True)
    except PermissionError:
        # Fallback to user's home directory if /var/log is not accessible
        log_dir = os.path.expanduser("~/crypto_market_bot_logs")
        os.makedirs(log_dir, mode=0o755, exist_ok=True)
    
    log_file = os.path.join(log_dir, "crypto_market_bot.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_file}")
