import logging
from telegram import Update
from telegram.ext import ContextTypes

# Database calls
from storage_manager import StorageManager, DATABASE
from features.group_khetma.khetma_storage import KhetmaStorage

# Local modules
from bot_setup import bot_app
from handlers import *

# 1. Create a logger object for this specific file
logger = logging.getLogger(__name__)

# 2. Write your "Middleware" function
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error globally and send a fallback message if needed."""
    
    error = context.error
    
    # Log the exact error and line number centrally to bot_activity.log
    logger.error(f"An error occurred: {error}", exc_info=True)
    
    # (Optional) Send a generic fallback message to the user
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("عذراً، حدث خطأ غير متوقع في النظام. تم إبلاغ المطور.")

def main(argv=None):
    # 1. Configure the logging system globally (FIRST THING!)
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO, # Ignore DEBUG, record everything INFO and above
        handlers=[
            logging.FileHandler("bot_activity.log", encoding='utf-8'), # Save to file safely
            logging.StreamHandler() # Also print to your VS Code terminal
        ]
    )

    # Attach the global error middleware
    bot_app.add_error_handler(global_error_handler)
    
    # Initialize Database
    db_core = StorageManager(DATABASE)
    
    # Khetma feature storage wrapper
    khetma_storage_engine = KhetmaStorage(db_core)

    # ==================================================================
    # INJECTIONS:
    # We put our storage engines into the bot's "backpack" (bot_data).
    # Now it travels with the bot everywhere.
    # ==================================================================
    bot_app.bot_data["khetma_storage"] = khetma_storage_engine
    
    # Register your command and message handlers
    main_commands_handler()
        
    logger.info("Starting Telegram Bot...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()