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

    def create_new_khetma(self, chat_id) -> Khetma:
        # 1. Ensure the Parent exists (The "Safety Net")
        sql_parent = "INSERT OR IGNORE INTO chats (chat_id) VALUES (?)"
        
        # 2. Insert the Child (The actual Khetma)
        sql_child = """
            INSERT INTO khetmat (chat_id, number, status)
            VALUES (?, ?, 'ACTIVE')
        """
        khetma_num = self.calc_next_khetma_number(chat_id)

        with self.db.connect_to_db() as conn:
            # We run both commands in ONE transaction
            cursor = conn.execute(sql_parent, (chat_id,))
            cursor = conn.execute(sql_child, (chat_id, khetma_num))

            khetma_id = cursor.lastrowid

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
                
                khetmat_list.append(Khetma.from_dict(khetma_dict))

            return khetmat_list  # Returns a list of khetmat objetcs

    def get_khetma(self, khetma_id, chat_id, status: str) -> Khetma | None:
        """
        Fetches a single specific Khetma directly from the DB.
        """
        sql = """
            SELECT * FROM khetmat 
            WHERE khetma_id = ? AND chat_id = ? AND status = ?
        """
        
        with self.db.connect_to_db() as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.execute(sql, (khetma_id, chat_id, status.upper()))
            row = cursor.fetchone()  # Get only the first result (or None)

            if row is None:
                return None

            # Parse the single row found
            khetma_dict = {
                str(row["khetma_id"]): {
                    "number": row["number"],
                    "status": row["status"],
                    "empty_chapters": json.loads(row["empty_chapters"]),
                    "reserved_chapters": json.loads(row["reserved_chapters"]),
                    "finished_chapters": json.loads(row["finished_chapters"])
                }
            }
            
            return Khetma.from_dict(khetma_dict)
        
    def get_available_chapters(self, chat_id) -> Dict[str, List[int]]:
        available_chapters = {}
        active_khetmat_list = self.get_chat_khetmat(chat_id, "ACTIVE")
        
        for khetma in active_khetmat_list:
            available_chapters[str(khetma.khetma_id)] = [chapter.number for chapter in khetma.get_available_chapters()]

        return available_chapters

    def update_khetma(self, chat_id, khetma_to_save: Khetma):
        khetma_dict = khetma_to_save.to_dict()
        khetma_id = next(iter(khetma_dict))
        status = khetma_dict[khetma_id]["status"].upper()
        number = khetma_dict[khetma_id]["number"]
        empty_chapters_json = json.dumps(khetma_dict[khetma_id]["empty_chapters"])
        reserved_chapters_json = json.dumps(khetma_dict[khetma_id]["reserved_chapters"])
        finished_chapters_json = json.dumps(khetma_dict[khetma_id]["finished_chapters"])
        
        sql_command = """
            UPDATE khetmat 
            SET number = ?,
                status = ?, 
                empty_chapters = ?, 
                reserved_chapters = ?, 
                finished_chapters = ?
            WHERE chat_id = ? AND khetma_id = ?
        """

        with self.db.connect_to_db() as conn:
            conn.execute(sql_command, (
                number,
                status, 
                empty_chapters_json, 
                reserved_chapters_json, 
                finished_chapters_json, 
                chat_id,    
                khetma_id   
            ))
            conn.commit()

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
        
    def assign_chapter_to_user(self, khetma_id, chat_id, chapter_num, user_id):
        khetma = self.get_active_khetma(khetma_id, chat_id)

        if khetma is None:
            return False

        chapter = khetma.get_chapter(chapter_num)

        if chapter.is_available:
            chapter.reserve(user_id)
            self.update_khetma(chat_id, khetma)
            return True
        else:
            return False