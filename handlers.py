from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Local imports
from main_commands import start_command, help_command, settings_command
from features.group_khetma.khetma_handlers import *
from bot_setup import bot_app

def main_commands_handler():
    # /start
    bot_app.add_handler(CommandHandler("start", start_command))

def khetma_handlers(): 
    # Khetma Feature Handlers
    bot_app.add_handler(CommandHandler("new_khetma", start_khetma_command))

    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finish_message_handler))

    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^reserve_"))
    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^info_"))