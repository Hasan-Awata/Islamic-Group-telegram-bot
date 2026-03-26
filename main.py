import logging
import os
from telegram import Update
from telegram import error as TelegramErrors
from telegram.ext import ContextTypes, ApplicationHandlerStop, TypeHandler

# Database calls
from storage_manager import StorageManager
from features.group_khetma.khetma_storage import KhetmaStorage
from features.group_khetma import errors

# Local modules
from bot_setup import bot_app, WEBHOOK_URL
from handlers import *

# 1. Create a logger object for this specific file
logger = logging.getLogger(__name__)

# 2. Write your "Middleware" function
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log the error globally and send a fallback message if needed."""
    
    error = context.error
    
    # IGNORE: BadRequest errors
    if isinstance(error, TelegramErrors.BadRequest):
        return

    # IGNORE: Custom errors
    if isinstance(error, errors.KhetmaError):
        return

    # Log the exact error and line number centrally to bot_activity.log
    logger.error(f"An error occurred: {error}", exc_info=True)

    # (Optional) Send a generic fallback message to the user
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("عذراً، حدث خطأ غير متوقع في النظام. تم إبلاغ المطور.")

async def activation_gatekeeper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts all updates and drops them if the group is inactive (Using Cache)."""
    
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id

    if update.message and update.message.text and update.message.text.startswith("/activate"):
        return 

    # 1. Initialize the cache in the bot's memory if it doesn't exist yet
    if "active_chats_cache" not in context.bot_data:
        context.bot_data["active_chats_cache"] = {}

    cache = context.bot_data["active_chats_cache"]

    # 2. Check if we already know the answer from RAM
    if chat_id in cache:
        is_active = cache[chat_id]
    else:
        # 3. We don't know yet. Ask the database ONLY ONCE.
        storage: KhetmaStorage = context.bot_data.get("khetma_storage")
        is_active = storage.is_chat_active(chat_id) if storage else False
        
        # Save the answer in RAM for next time
        cache[chat_id] = is_active

    # 4. Drop the message instantly if the group isn't active
    if not is_active:
        raise ApplicationHandlerStop
        
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

    # Attach the Gatekeeper
    bot_app.add_handler(TypeHandler(Update, activation_gatekeeper), group=-1) # Force to run first (group=-1)

    # Attach the global error middleware
    bot_app.add_error_handler(global_error_handler)
    
    # Initialize Database
    db_core = StorageManager()
    
    # Khetma feature storage wrapper
    khetma_storage_engine = KhetmaStorage(db_core)

    # ==================================================================
    # INJECTIONS:
    # We put our storage engines into the bot's "backpack" (bot_data).
    # Now it travels with the bot everywhere.
    # ==================================================================
    bot_app.bot_data["khetma_storage"] = khetma_storage_engine
    
    # Main commands:
    main_commands_handler()
    
    # Feature/ Khetma(Group reading session):
    khetma_handlers()
    
    logger.info("Starting Telegram Bot...")

    # bot_app.run_polling(drop_pending_updates=True) # For local testing ...

    bot_app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8443)),
    webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()