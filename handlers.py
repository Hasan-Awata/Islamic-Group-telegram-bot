from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Local imports
from main_commands import *
from features.group_khetma.khetma_handlers import *

def main_commands_handler():
    # /start
    bot_app.add_handler(CommandHandler("start", start_command))

def khetma_handlers():
    # Base commands
    bot_app.add_handler(CommandHandler("start", start_command))
    
    # Khetma Feature Handlers
    bot_app.add_handler(CommandHandler("new_khetma", start_khetma_command))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finish_message_handler))
    bot_app.add_handler(CallbackQueryHandler(handle_button_reserve, pattern="^reserve_"))