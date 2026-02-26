import sqlite3
from contextlib import contextmanager

DATABASE = 'bot_database.db'

class StorageManager:
    def __init__(self, db_path=DATABASE):
        self.db_path = db_path
        self._init_chats_table()
        
    def connect_to_db(self):
        return sqlite3.connect(self.db_path)
    
    @contextmanager
    def managed_connection(self):
        """
        A custom context manager that automatically commits/rollbacks
        AND closes the db connection when the block ends.
        """
        conn = self.connect_to_db()
        try:
            # The inner 'with' handles commit/rollback
            with conn:
                yield conn
        finally:
            # The finally block guarantees the file is closed for Windows
            conn.close()

    def _init_chats_table(self):
        with self.managed_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chats(
                    chat_id INTEGER PRIMARY KEY
                )
            ''')
