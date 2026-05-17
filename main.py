import logging
import asyncio
from bot.telegram_bot import setup_bot
from utils.keep_alive import keep_alive

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Content Studio...")
    
    # Start the dummy web server for Render compatibility
    keep_alive()
    
    application = setup_bot()
    
    logger.info("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
