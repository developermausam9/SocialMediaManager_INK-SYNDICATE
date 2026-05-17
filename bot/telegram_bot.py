import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config.settings import settings
from bot.handlers import start_command, generate_command, button_callback

logger = logging.getLogger(__name__)

def setup_bot():
    if settings.TELEGRAM_BOT_TOKEN == 'your_token' or not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bot will fail to start.")
    
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    return application
