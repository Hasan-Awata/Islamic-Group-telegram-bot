from telegram.ext import CommandHandler, MessageHandler, filters

from bot_setup import bot_app
from handlers import *

def main(argv=None):
    # print("Initializing Bot Database...")
    # storage_manager.init_history_table()
    # game_poetry_contest.init_poetry_contest_game_table()
    # print("Database was initialized successfully...")

    command_handlers()
        
    # # When user types /help -> run help_command()
    # bot_app.add_handler(CommandHandler("help", help_command))
    
    # # When user types /clear -> run clear_command()
    # bot_app.add_handler(CommandHandler("clear", clear_command))

    # # When user types /translate -> run translate_command()
    # bot_app.add_handler(CommandHandler("translate", translate_command))

    # # When user types /games -> run games_command()
    # bot_app.add_handler(CommandHandler("games", games_command))

    # # Register the games callback handlers (Must be BEFORE MessageHandler)
    # bot_app.add_handlers(games_handlers)

    # # When user sends Text AND it is NOT a command -> run handle_message()
    # # (The tilde '~' means NOT)
    # bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Dullani Bot Running...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
