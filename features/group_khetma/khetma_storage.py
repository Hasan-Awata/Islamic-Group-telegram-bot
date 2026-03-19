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
        with self.db.managed_connection() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS khetmat(
                    khetma_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
                    number INTEGER NOT NULL,
                    status TEXT CHECK(status IN ('ACTIVE', 'FINISHED')) DEFAULT 'ACTIVE'
                );
            ''')

    def _init_chapters_table(self):
        with self.db.managed_connection() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chapters (
                chapter_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                khetma_id INTEGER NOT NULL REFERENCES khetmat(khetma_id) ON DELETE CASCADE,
                number INTEGER NOT NULL,
                status TEXT DEFAULT 'EMPTY', 
                owner_id BIGINT,          
                owner_username TEXT                                    
                );
            ''')

    def create_new_khetma(self, chat_id) -> Khetma:
        sql_insert_chat = "INSERT INTO chats (chat_id) VALUES (%s) ON CONFLICT DO NOTHING"
        
        sql_insert_khetma = """
            INSERT INTO khetmat (chat_id, number, status)
            VALUES (%s, COALESCE((SELECT MAX(number) FROM khetmat WHERE chat_id = %s), 0) + 1, 'ACTIVE')
            RETURNING khetma_id, number
        """

        sql_insert_chapters = "INSERT INTO chapters (khetma_id, number, status) VALUES (%s, %s, 'EMPTY')"

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_insert_chat, (chat_id,))
            cursor.execute(sql_insert_khetma, (chat_id, chat_id))
            row = cursor.fetchone()
            khetma_id = row["khetma_id"]
            khetma_num = row["number"]

            chapters_data = [(khetma_id, num) for num in range(1, 31)]
            cursor.executemany(sql_insert_chapters, chapters_data)

            return Khetma(khetma_id, khetma_num, Khetma.khetma_status.ACTIVE)
        
    def get_khetma(self, khetma_id=None, khetma_number=None, chat_id=None) -> Khetma | None:
        """
        Fetches a single specific Khetma directly from the DB.
        """
        sql_khetma_command = "SELECT * FROM khetmat" 
        params = []
        conditions = []

        if khetma_id:
            conditions.append("khetma_id = %s")
            params.append(khetma_id)
        if khetma_number:
            conditions.append("number = %s")
            params.append(khetma_number)
        if chat_id:
            conditions.append("chat_id = %s")
            params.append(chat_id)

        if conditions:
            sql_khetma_command += " WHERE " + " AND ".join(conditions)
        else:
            return None 

        sql_chapters_command = "SELECT * FROM chapters WHERE khetma_id = %s ORDER BY number ASC"

        with self.db.managed_connection() as cursor:
            
            # A. Fetch Khetma
            cursor.execute(sql_khetma_command, params)
            khetma_row = cursor.fetchone()

            if khetma_row is None:
                return None
            
            # B. Fetch Chapters
            cursor.execute(sql_chapters_command, (khetma_row["khetma_id"],))
            chapters_rows = cursor.fetchall()

        return Khetma.from_db_row(khetma_row, chapters_rows)
    
    def get_khetmat_by_ids(self, khetma_ids: list) -> dict:
        """Returns a dict of {khetma_id: khetma_number} for a list of IDs."""

        placeholders = ",".join(["%s"] * len(khetma_ids))
        sql = f"SELECT khetma_id, number FROM khetmat WHERE khetma_id IN ({placeholders})"
        
        with self.db.managed_connection() as cursor:
            cursor.execute(sql, tuple(khetma_ids))
            return {row["khetma_id"]: row["number"] for row in cursor.fetchall()}
    
    def get_active_khetmat(self, chat_id) -> list[Khetma]:
        """Returns all ACTIVE khetmat in a chat with their chapters."""
        sql_khetmat = "SELECT * FROM khetmat WHERE chat_id = %s AND status = 'ACTIVE'"

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_khetmat, (chat_id,))
            khetma_rows = cursor.fetchall()

            if not khetma_rows:
                return []

            khetma_ids = [row["khetma_id"] for row in khetma_rows]
            placeholders = ",".join(["%s"] * len(khetma_ids))
            cursor.execute(
                f"SELECT * FROM chapters WHERE khetma_id IN ({placeholders}) ORDER BY khetma_id, number ASC",
                tuple(khetma_ids)
            )
            chapters_rows = cursor.fetchall()

        # Group chapters by khetma_id
        chapters_by_khetma = {}
        for ch_row in chapters_rows:
            chapters_by_khetma.setdefault(ch_row["khetma_id"], []).append(ch_row)

        return [
            Khetma.from_db_row(khetma_row, chapters_by_khetma.get(khetma_row["khetma_id"], []))
            for khetma_row in khetma_rows
        ]
    
    def get_chapter(self, chapter_id=None, khetma_id=None, chapter_number=None) -> Chapter | None:
        """
        Fetches a single specific Chapter directly from the DB.
        """
        sql_chapter_command = "SELECT * FROM chapters" 
        params = []
        conditions = []

        if chapter_id:
            conditions.append("chapter_id = %s")
            params.append(chapter_id)
        if khetma_id:
            conditions.append("khetma_id = %s")
            params.append(khetma_id)
        if chapter_number:
            conditions.append("number = %s")
            params.append(chapter_number)

        if conditions:
            sql_chapter_command += " WHERE " + " AND ".join(conditions)
        else:
            return None 

        with self.db.managed_connection() as cursor:
            
            cursor.execute(sql_chapter_command, params)
            chapter_row = cursor.fetchone()

            if not chapter_row:
                return None

        return Chapter.from_db_row(chapter_row)

    def get_chapters_by_user(self, user_id, chat_id=None, khetma_id=None) -> list[Chapter]:
        
        sql_command = """
            SELECT * FROM chapters 
            WHERE owner_id = %s
            AND status = 'RESERVED'
        """
        params = [user_id]
        
        if chat_id:
            sql_command += " AND khetma_id IN (SELECT khetma_id FROM khetmat WHERE chat_id = %s)"
            params.append(chat_id)

        if khetma_id:
            sql_command += " AND khetma_id = %s"
            params.append(khetma_id)

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, params)
            rows = cursor.fetchall()

            if not rows:
                raise errors.NoOwnedChapters()
            
            return [Chapter.from_db_row(row) for row in rows]

    def update_khetma(self, khetma: Khetma):
        
        sql_command = """
            UPDATE khetmat 
            SET status = %s,
            number = %s
            WHERE khetma_id = %s
        """

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, (khetma.status.value.upper(), khetma.number, khetma.khetma_id))
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
            SET status = %s, owner_id = %s, owner_username = %s
            WHERE khetma_id = %s AND number = %s
        """
        
        with self.db.managed_connection() as cursor:
            data_to_update = [
                (chapter.status.value.upper(), chapter.owner_id, chapter.owner_username, chapter.parent_khetma, chapter.number)
                for chapter in chapters
            ]
            
            # This works perfectly whether the list has 1 item or 30 items
            cursor.executemany(sql_command, data_to_update)
            
            return cursor.rowcount > 0

    def reserve_chapter(self, khetma_id, chapter_number, user_id, username) -> bool:
        sql_command = """
            UPDATE chapters
            SET status = 'RESERVED', owner_id = %s, owner_username = %s
            WHERE khetma_id = %s AND number = %s AND status = 'EMPTY' 
        """
        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, (user_id, username, khetma_id, chapter_number))
            if cursor.rowcount > 0:
                return True
            
        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)

        if chapter.is_reserved:
            raise errors.ChapterAlreadyReservedError()
        elif chapter.is_finished: 
            raise errors.ChapterFinishedError()

    def withdraw_chapter(self, khetma_id, chapter_number, user_id, is_admin=False) -> bool:
        sql_command = """
            UPDATE chapters
            SET status = 'EMPTY', owner_id = NULL, owner_username = NULL
            WHERE khetma_id = %s AND number = %s AND status = 'RESERVED'
        """
        params = [khetma_id, chapter_number] 

        if not is_admin:
            sql_command += " AND owner_id = %s"
            params.append(user_id) 

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, params)
            if cursor.rowcount > 0:
                return True
            
        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)
        if chapter.is_available:
            raise errors.ChapterAlreadyEmptyError()
        elif chapter.is_finished: 
            raise errors.ChapterFinishedError()
        elif chapter.is_reserved and not is_admin:
            if user_id != chapter.owner_id:
                raise errors.ChapterNotOwnedError()

    def withdraw_all_user_chapters(self, chat_id, user_id, khetma_id=None) -> list[Chapter]:
        sql_command = """
            UPDATE chapters
            SET status = 'EMPTY', owner_id = NULL, owner_username = NULL
            WHERE owner_id = %s
            AND status = 'RESERVED'
            AND khetma_id IN (SELECT khetma_id FROM khetmat WHERE chat_id = %s)
        """
        params = [user_id, chat_id]

        if khetma_id:
            sql_command += " AND khetma_id = %s"
            params.append(khetma_id)

        sql_command += " RETURNING *"

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, params)
            rows = cursor.fetchall()
            if not rows:
                raise errors.NoOwnedChapters()

            return [Chapter.from_db_row(row) for row in rows]
    
    def finish_chapter(self, khetma_id, chapter_number, user_id, username) -> bool:
        sql_command = """
            UPDATE chapters
            SET status = 'FINISHED', owner_id = %s, owner_username = %s
            WHERE khetma_id = %s AND number = %s 
            AND (status = 'EMPTY' OR (status = 'RESERVED' AND owner_id = %s))
        """
        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, (user_id, username, khetma_id, chapter_number, user_id))
            if cursor.rowcount > 0:
                return True

        chapter = self.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)

        if chapter.is_finished:
            raise errors.ChapterFinishedError()
        elif chapter.is_reserved and user_id != chapter.owner_id:
            raise errors.ChapterNotOwnedError()
    
    def finish_all_user_chapters(self, chat_id, user_id, khetma_id=None) -> list[Chapter]:
        sql_command = """
            UPDATE chapters
            SET status = 'FINISHED'
            WHERE owner_id = %s 
            AND status = 'RESERVED'
            AND khetma_id IN (SELECT khetma_id FROM khetmat WHERE chat_id = %s)
        """
        params = [user_id, chat_id] 

        if khetma_id:
            sql_command += " AND khetma_id = %s"
            params.append(khetma_id)

        sql_command += " RETURNING *"

        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, params)
            rows = cursor.fetchall()
            if not rows:
                raise errors.NoOwnedChapters()

            return [Chapter.from_db_row(row) for row in rows]
        
    def calc_finished_khetmat_number(self, chat_id) -> int:
        sql_command = "SELECT COUNT(*) AS total FROM khetmat WHERE chat_id = %s AND status = 'FINISHED'"
        
        with self.db.managed_connection() as cursor:
            cursor.execute(sql_command, (chat_id,))
            count = cursor.fetchone()["total"]
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
        sql = "SELECT COALESCE(MAX(number), 0) + 1 AS next_num FROM khetmat WHERE chat_id = %s"
        
        with self.db.managed_connection() as cursor:
            cursor.execute(sql, (chat_id,))
            return cursor.fetchone()["next_num"]
        

