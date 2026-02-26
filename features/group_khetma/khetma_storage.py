import sqlite3
from typing import List, Dict, Any

# Local modules
import storage_manager
import features.group_khetma.errors as errors
from features.group_khetma.class_khetma import Khetma
from features.group_khetma.class_chapter import Chapter

class KhetmaStorage:
    def __init__(self, db_core: storage_manager.StorageManager):
        self.db = db_core
        self._init_khetma_table()
        self._init_chapters_table()
    
    def _init_khetma_table(self):
        with self.db.managed_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS khetmat(
                    khetma_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    status TEXT CHECK(status IN ('ACTIVE', 'FINISHED')) DEFAULT 'ACTIVE',

                    FOREIGN KEY (chat_id) REFERENCES chats(chat_id) ON DELETE CASCADE
                );
            ''')

    def _init_chapters_table(self):
        with self.db.managed_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                chapter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                khetma_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                status TEXT DEFAULT 'EMPTY', -- 'EMPTY', 'RESERVED', 'FINISHED'
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
            INSERT INTO chapters (khetma_id, number, status)
            VALUES (?, ?, 'EMPTY')
        """
        khetma_num = self.calc_next_khetma_number(chat_id)

        with self.db.managed_connection() as conn:
            cursor = conn.execute(sql_insert_chat, (chat_id,))
            cursor = conn.execute(sql_insert_khetma, (chat_id, khetma_num))
            khetma_id = cursor.lastrowid

            chapters_data = [(khetma_id, chat_num) for chat_num in range(1, 31)]

            cursor = conn.executemany(sql_insert_chapters, chapters_data)

            return Khetma(khetma_id, khetma_num, Khetma.khetma_status.ACTIVE)
        
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

        with self.db.managed_connection() as conn:
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

        with self.db.managed_connection() as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            
            chapter_cursor = conn.execute(sql_chapter_command, params)
            chapter_row = chapter_cursor.fetchone()

            if not chapter_row:
                return None

        return Chapter(
            parent_khetma=chapter_row["khetma_id"],
            number=chapter_row["number"],
            owner_id=chapter_row["owner_id"],
            owner_username=chapter_row["owner_username"], 
            status=Chapter.chapter_status[chapter_row["status"].upper()]
        )

    def get_chapters_by_user(self, user_id, khetma_id=None) -> list[Chapter]:
        
        sql_command = "SELECT * FROM chapters WHERE owner_id = ?"
        params = [user_id]
        
        if khetma_id:
            sql_command += " AND khetma_id= ?"
            params.append(khetma_id)

        with self.db.managed_connection() as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            
            cursor = conn.execute(sql_command, params)
            rows = cursor.fetchall()

            if not rows:
                raise errors.NoOwnedChapters()
            
            chapters_list = []
            for row in rows:
                chapter = Chapter.from_db_row(row)
                chapters_list.append(chapter)

            return chapters_list 

    def update_khetma(self, khetma: Khetma):
        
        sql_command = """
            UPDATE khetmat 
            SET status = ?,
            number = ?
            WHERE khetma_id = ?
        """

        with self.db.managed_connection() as conn:
            cursor = conn.execute(sql_command, (khetma.status.value.upper(), khetma.number, khetma.khetma_id))
            return cursor.rowcount > 0 # True: the updating succeeded, Flase: the update failed
        
    def update_chapters(self, chapters: list[Chapter] | Chapter) -> bool:

        # 1. Normalize the input: If it's a single object, make it a list of one.
        if isinstance(chapters, Chapter):
            chapters = [chapters]
            
        # 2. Safety check
        if not chapters:
            return False
            
        # 3. Exactly ONE SQL string and ONE execution path
        sql_command = """
            UPDATE chapters 
            SET status = ?, owner_id = ?, owner_username = ?
            WHERE khetma_id = ? AND number = ?
        """
        
        with self.db.managed_connection() as conn:
            data_to_update = [
                (chapter.status.value.upper(), chapter.owner_id, chapter.owner_username, chapter.parent_khetma, chapter.number)
                for chapter in chapters
            ]
            
            # This works perfectly whether the list has 1 item or 30 items
            cursor = conn.executemany(sql_command, data_to_update)
            
            return cursor.rowcount > 0

    def reserve_chapter(self, khetma_id, chapter_number, user_id, username) -> bool:
        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)
        if chapter.is_reserved:
            raise errors.ChapterAlreadyReservedError()
        elif chapter.is_finished: 
            raise errors.ChapterFinishedError()
        else:
            chapter.reserve(user_id, username)
            self.update_chapters(chapter)
            return True

    def withdraw_chapter(self, khetma_id, chapter_number, user_id, is_admin=False) -> bool:
        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)
        if chapter.is_available:
            raise errors.ChapterAlreadyEmptyError()
        elif chapter.is_finished and not is_admin: 
            raise errors.ChapterFinishedError()
        elif chapter.is_reserved and not is_admin:
            if user_id != chapter.owner_id:
                raise errors.ChapterNotOwnedError()
        chapter.mark_empty()
        self.update_chapters(chapter)
        return True
    
    def finish_chapter(self, khetma_id, chapter_number, user_id, username) -> bool:
        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)

        if chapter.is_finished:
            raise errors.ChapterFinishedError()
        elif chapter.is_reserved and user_id != chapter.owner_id:
            raise errors.ChapterNotOwnedError()
        elif chapter.is_available:
            chapter.reserve(user_id, username)

        chapter.mark_finished()

        if not self.update_chapters(chapter):
            raise errors.DatabaseConnectionError()
            
        return True
    
    def finish_all_user_chapters(self, user_id, username, khetma_id=None) -> tuple[list[Chapter], list[Chapter]]:
        try:
            chapters = self.get_chapters_by_user(user_id, khetma_id)
        except errors.NoOwnedChapters:
            raise errors.NoOwnedChapters()
            
        success = [] # A list of chapters that were finished successfully
        failed = [] # A list of tuples contains the chapter that failed to finish with its error message

        for chapter in chapters:
            if chapter.is_finished:
                failed.append((chapter, errors.ChapterFinishedError()))
                continue 
            elif chapter.is_reserved and user_id != chapter.owner_id:
                failed.append((chapter, errors.ChapterNotOwnedError()))
                continue 
            elif chapter.is_available:
                chapter.reserve(user_id, username)

            chapter.mark_finished()
            success.append(chapter)
        
        if success:
            if not self.update_chapters(success):
                raise errors.DatabaseConnectionError()
        
        return success, failed 

    def calc_finished_khetmat_number(self, chat_id) -> int:
        sql_command = "SELECT COUNT(*) FROM khetmat WHERE chat_id = ? and status = 'FINISHED'"
        
        with self.db.managed_connection() as conn:
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
        
        with self.db.managed_connection() as conn:
            cursor = conn.execute(sql, (chat_id,))
            return cursor.fetchone()[0]
        

