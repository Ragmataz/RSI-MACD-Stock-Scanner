import os
import logging
import time
from scanner.scanner import run

def setup_logging():
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up file and console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/scanner_{time.strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_logging()
    
    # Check if environment variables are set
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logging.warning("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        logging.info("You can set them in your environment or create a .env file")
        exit(1)
    
    logging.info("Starting RSI & MACD Stock Scanner")
    try:
        run()
        logging.info("Scan completed successfully")
    except Exception as e:
        logging.error(f"Error during scan: {e}")
    finally:
        logging.info("Scanner process finished")
