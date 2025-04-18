import os
import logging
from scanner.scanner import run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # Check if environment variables are set
    if not os.getenv("TELEGRAM_BOT_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logging.warning("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        logging.info("You can set them in your environment or create a .env file")
        exit(1)
    
    logging.info("Starting RSI & MACD Stock Scanner")
    run()
    logging.info("Scan completed")
