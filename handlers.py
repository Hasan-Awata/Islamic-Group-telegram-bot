from telegram.ext import CommandHandler
from commands import *

def command_handlers():
    # When user types /start -> run start_command()
    bot_app.add_handler(CommandHandler("start", start_command))
