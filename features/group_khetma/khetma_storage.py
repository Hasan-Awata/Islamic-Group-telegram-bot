import sqlite3
import json
from typing import List, Dict, Any

# Local modules
import storage_manager
from class_khetma import Khetma
from class_chapter import Chapter

class KhetmaStorage:
    def __init__(self, db_core: storage_manager.StorageManager):
        self.db = db_core
        self._init_khetma_table()
        self._init_chapters_table
    
    def _init_khetma_table(self):
        with self.db.connect_to_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS khetmat(
                    khetma_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    status TEXT CHECK(status IN ('ACTIVE', 'FINISHED')) DEFAULT 'ACTIVE',
                    empty_chapters TEXT DEFAULT '[]', -- only a list of numbers since we have no crucial data yet.
                    reserved_chapters TEXT DEFAULT '{}', -- a list of dictionaries that shows the owner beside number.
                    finished_chapters TEXT DEFAULT '{}', 

                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
                );
            ''')

    def _init_chapters_table(self):
        with self.db.connect_to_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                khetma_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                status TEXT DEFAULT 'AVAILABLE', -- 'EMPTY', 'RESERVED', 'FINISHED'
                owner_id INTEGER,          -- NULL if empty
                owner_username TEXT,           -- NULL if empty
                         
                FOREIGN KEY(khetma_id) REFERENCES khetmat(khetma_id) ON DELETE CASCADE
                );
            ''')

    def create_new_khetma(self, chat_id) -> Khetma:
        # 1. Ensure the Parent exists (The "Safety Net")
        sql_insert_chat = "INSERT OR IGNORE INTO chats (chat_id) VALUES (?)"
        
        # 2. Insert the Child (The actual Khetma)
        sql_insert_khetma = """
            INSERT INTO khetmat (chat_id, number, status)
            VALUES (?, ?, 'ACTIVE')
        """

        sql_insert_chapters = """
            INSERT INTO chapters (chat_id, khetma_id, number, status)
            VALUES (?, ?, ?, 'EMPTY')
        """
        khetma_num = self.calc_next_khetma_number(chat_id)

        with self.db.connect_to_db() as conn:
            cursor = conn.execute(sql_insert_chat, (chat_id,))
            cursor = conn.execute(sql_insert_khetma, (chat_id, khetma_num))
            khetma_id = cursor.lastrowid

            chapters_data = [(chat_id, khetma_id, chat_num) for chat_num in range(1, 31)]

            cursor = conn.executemany(sql_insert_chapters, chapters_data)


            conn.commit()

            return Khetma(khetma_id, khetma_num, Khetma.khetma_status.ACTIVE)
        
    def get_chat_khetmat(self, chat_id, status_str: str) -> list[Khetma]:
        """Fetches ALL finished Khetmat for a specific chat as a list of khetma objects."""
        sql = """
            SELECT * FROM khetmat 
            WHERE chat_id = ? AND status = ?
        """
        
        with self.db.connect_to_db() as conn:
            # Enable accessing columns by name
            conn.row_factory = sqlite3.Row 
            cursor = conn.execute(sql, (chat_id, status_str))
            rows = cursor.fetchall() 

            khetmat_list = []

            for row in rows:
                khetma_dict = {
                    str(row["khetma_id"]): {
                    "number": row["number"],
                    "status": row["status"],
                    # Decode JSON text back into Python Lists for each row
                    "empty_chapters": json.loads(row["empty_chapters"]),
                    "reserved_chapters": json.loads(row["reserved_chapters"]),
                    "finished_chapters": json.loads(row["finished_chapters"])
                    }
                }
                
                khetmat_list.append(Khetma.from_db_row(khetma_dict))

            return khetmat_list  # Returns a list of khetmat objetcs

    def get_khetma(self, khetma_id=None, khetma_number=None, chat_id=None) -> Khetma | None:
        """
        Fetches a single specific Khetma directly from the DB.
        """
        sql_khetma_command = "SELECT * FROM khetmat" 
        params = []
        conditions = []

        if khetma_id:
            conditions.append("khetma_id = ?")
            params.append(khetma_id)
        if khetma_number:
            conditions.append("number = ?")
            params.append(khetma_number)
        if chat_id:
            conditions.append("chat_id = ?")
            params.append(chat_id)

        if conditions:
            sql_khetma_command += " WHERE " + " AND ".join(conditions)
        else:
            return None 

        sql_chapters_command = "SELECT * FROM chapters WHERE khetma_id = ? ORDER BY number ASC"

        with self.db.connect_to_db() as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            
            # A. Fetch Khetma
            khetma_cursor = conn.execute(sql_khetma_command, params)
            khetma_row = khetma_cursor.fetchone()

            if khetma_row is None:
                return None
            
            # B. Fetch Chapters
            chapter_cursor = conn.execute(sql_chapters_command, (khetma_row["khetma_id"],))
            chapters_rows = chapter_cursor.fetchall()

        chapters_list = []
        for ch_row in chapters_rows:
            chapter = Chapter(
                number=ch_row["number"],
                owner_id=ch_row["owner_id"],
                owner_username=ch_row["owner_username"], 
                status=Chapter.chapter_status[ch_row["status"].upper()]
            )
            chapters_list.append(chapter)

        return Khetma(
            khetma_id=khetma_row["khetma_id"],
            number=khetma_row["number"],
            status=Khetma.khetma_status[khetma_row["status"].upper()],
            chapters=chapters_list
        )

    def get_chapter(self, chapter_id=None, khetma_id=None, chapter_number=None) -> Chapter | None:
        """
        Fetches a single specific Chapter directly from the DB.
        """
        sql_chapter_command = "SELECT * FROM chapters" 
        params = []
        conditions = []

        if chapter_id:
            conditions.append("chapter_id = ?")
            params.append(chapter_id)
        if khetma_id:
            conditions.append("khetma_id = ?")
            params.append(khetma_id)
        if chapter_number:
            conditions.append("number = ?")
            params.append(chapter_number)

        if conditions:
            sql_chapter_command += " WHERE " + " AND ".join(conditions)
        else:
            return None 

        with self.db.connect_to_db() as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            
            # A. Fetch Chapter
            chapter_cursor = conn.execute(sql_chapter_command, params)
            chapter_row = chapter_cursor.fetchone()

            if chapter_row is None:
                return None

        return Chapter(
            number=chapter_row["number"],
            owner_id=chapter_row["owner_id"],
            owner_username=chapter_row["owner_username"], 
            status=Chapter.chapter_status[chapter_row["status"].upper()]
        )

    def calc_finished_khetmat_number(self, chat_id) -> int:
        sql_command = "SELECT COUNT(*) FROM khetmat WHERE chat_id = ? and status = 'FINISHED'"
        
        with self.db.connect_to_db() as conn:
            cursor = conn.execute(sql_command, (chat_id,))
            count = cursor.fetchone()[0]
            return count + 1
    
    def calc_next_khetma_number(self, chat_id: int) -> int:
        """
        Calculates the next sequence number for a Khetma in this chat.
        Logic: Finds the highest existing number and adds 1.
        Returns: 1 if it's the first Khetma.
        """
        # COALESCE(MAX(number), 0) handles two cases:
        # 1. No khetmas exist -> MAX is NULL -> COALESCE returns 0 -> Result: 1
        # 2. Max is 5 -> Returns 5 -> Result: 6
        sql = "SELECT COALESCE(MAX(number), 0) + 1 FROM khetmat WHERE chat_id = ?"
        
        with self.db.connect_to_db() as conn:
            cursor = conn.execute(sql, (chat_id,))
            return cursor.fetchone()[0]
        

