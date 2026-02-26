import sqlite3
import json

DATABASE = 'bot_database.db'

class StorageManager:
    def __init__(self, db_path=DATABASE):
        self.db_path = db_path
        self._init_chats_table()
        
    def connect_to_db(self):
        return sqlite3.connect(self.db_path)
    
    def _init_chats_table(self):
        with self.connect_to_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chats(
                    chat_id INTEGER PRIMARY KEY,
                )
            ''')