import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from decouple import config

class StorageManager:
    def __init__(self):
        self.dsn = config("DATABASE_URL")
        self.pool = pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            dsn=self.dsn,
            cursor_factory=RealDictCursor
        )
        self._init_chats_table()

    @contextmanager
    def managed_connection(self):
        conn: psycopg2.extensions.connection = self.pool.getconn()
        cursor = None 
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            self.pool.putconn(conn)

    def _init_chats_table(self):
        with self.managed_connection() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats(
                    chat_id BIGINT PRIMARY KEY,
                    is_active BOOLEAN DEFAULT FALSE
                )
            ''')