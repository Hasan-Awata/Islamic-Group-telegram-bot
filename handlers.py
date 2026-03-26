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
    bot_app.add_handler(CommandHandler("activate", activate_command))
    bot_app.add_handler(CommandHandler("deactivate", deactivate_command))

    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, finish_message_handler), group=0)
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, my_chapters_handler), group=1)
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, available_chapters_handler), group=2)
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_withdraw_handler), group=3)
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, remind_handler), group=4)

    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^reserve"))
    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^info"))
    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^finish_all"))
    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^my_chapters"))
    bot_app.add_handler(CallbackQueryHandler(handle_khetma_buttons, pattern="^withdraw_all"))