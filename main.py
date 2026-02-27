from telegram.ext import CommandHandler, MessageHandler, filters

# Database calls
from storage_manager import StorageManager, DATABASE
from features.group_khetma.khetma_storage import KhetmaStorage

# Local modules
from bot_setup import bot_app
from handlers import *

def main(argv=None):
    db_core = StorageManager(DATABASE)
    
    # Khetma feature storage wrapper
    khetma_storage_engine = KhetmaStorage(db_core)

    # ==================================================================
    # INJECTIONS:
    # We put our storage engines into the bot's "backpack" (bot_data).
    # Now it travels with the bot everywhere.
    # ==================================================================
    bot_app.bot_data["khetma_storage"] = khetma_storage_engine
    
    main_commands_handler()
        
    print("Dullani Bot Running...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
