import os
import requests
import logging
import time

# Track sent messages to prevent duplicates
_last_message = None
_last_sent_time = 0

def send_telegram_message(message):
    global _last_message, _last_sent_time
    
    try:
        # Prevent duplicate messages
        current_time = time.time()
        if message == _last_message and (current_time - _last_sent_time) < 60:
            logging.warning("Duplicate message detected within 60 seconds. Not sending again.")
            return False
            
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logging.error("Telegram credentials missing. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
            return False
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Will raise an exception for 4XX/5XX responses
        
        # Update last message tracking
        _last_message = message
        _last_sent_time = current_time
        
        logging.info(f"Message sent successfully to Telegram")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")
        return False
