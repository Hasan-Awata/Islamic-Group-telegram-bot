import unittest
import os

# Local imports
from storage_manager import StorageManager
from features.group_khetma.khetma_storage import KhetmaStorage
from features.group_khetma import errors
from features.group_khetma import utilities

# python -m unittest -v testings.khetma_feature_testing

TEST_DB_NAME = "test_bot_database.sqlite"

class TestGroupKhetma(unittest.TestCase):
    def setUp(self):
        """Runs before EVERY test. Sets up a fresh, empty database."""
        # Remove the test DB if it accidentally got left behind
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)
            
        self.db_core = StorageManager(TEST_DB_NAME)
        self.storage = KhetmaStorage(self.db_core)
        
        # Fake Telegram Data
        self.chat_id = -100123456
        self.admin = {"id": 111, "username": "AdminGuy"}
        self.user_a = {"id": 222, "username": "UserA"}
        self.user_b = {"id": 333, "username": "UserB"}

    def tearDown(self):
        """Runs after EVERY test. Cleans up the test database."""
        if os.path.exists(TEST_DB_NAME):
            os.remove(TEST_DB_NAME)

    # ==========================================
    # 1. CORE KHETMA LOGIC TESTS
    # ==========================================
    def test_create_new_khetma(self):
        """Test if a new Khetma generates exactly 30 empty chapters."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        
        self.assertEqual(khetma.number, 1)
        self.assertEqual(khetma.status.name, "ACTIVE")
        self.assertEqual(len(khetma.chapters), 30)
        self.assertTrue(khetma.chapters[0].is_available)

    def test_reserve_chapter_success(self):
        """Test if a user can successfully reserve an available chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        
        success = self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.assertTrue(success)
        
        chapter_1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        self.assertTrue(chapter_1.is_reserved)
        self.assertEqual(chapter_1.owner_username, "UserA")

    def test_reserve_chapter_conflict(self):
        """Test if the system blocks a user from stealing a reserved chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        
        # User A reserves it first
        self.storage.reserve_chapter(khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"])
        
        # User B tries to reserve the exact same chapter
        with self.assertRaises(errors.ChapterAlreadyReservedError):
            self.storage.reserve_chapter(khetma.khetma_id, 1, self.user_b["id"], self.user_b["username"])

    def test_finish_chapter_ownership(self):
        """Test if a user can finish a chapter, and others are blocked from doing so."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"])
        
        # User B tries to finish User A's chapter
        with self.assertRaises(errors.ChapterNotOwnedError):
            self.storage.finish_chapter(khetma.khetma_id, 5, self.user_b["id"], self.user_b["username"])
            
        # User A finishes their own chapter
        success = self.storage.finish_chapter(khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"])
        self.assertTrue(success)
        
        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=5)
        self.assertTrue(chapter.is_finished)

    def test_finish_all_user_chapters(self):
        """Test the bulk finishing logic for a specific user."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        
        # User A reserves multiple parts
        self.storage.reserve_chapter(khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"])
        self.storage.reserve_chapter(khetma.khetma_id, 2, self.user_a["id"], self.user_a["username"])
        
        # Execute "تم أجزائي" logic
        finished = self.storage.finish_all_user_chapters(self.user_a["id"], self.user_a["username"])
        
        self.assertEqual(len(finished), 2)
        
        # Execute "تم أجزائي" logic again without any owned chapters
        with self.assertRaises(errors.NoOwnedChapters):
            self.storage.finish_all_user_chapters(self.user_a["id"], self.user_a["username"])

        # Verify in DB
        ch1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        ch2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)
        self.assertTrue(ch1.is_finished and ch2.is_finished)

    def test_withdraw_chapter(self):
        """Test if a user can free up a chapter they reserved."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(khetma.khetma_id, 10, self.user_a["id"], self.user_a["username"])
        
        self.storage.withdraw_chapter(khetma.khetma_id, 10, self.user_a["id"])
        
        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=10)
        self.assertTrue(chapter.is_available)

    # ==========================================
    # 2. UTILITY LOGIC TESTS
    # ==========================================
    def test_extract_arabic_numbers(self):
        """Test the natural language parser for Arabic text."""
        test_cases = {
            "تم 1": [1],
            "تم الجزء الأول": [1],
            "تم 1 و 30": [1, 30],
            "الجزء الخامس و العشرون": [25],
            "قرأت السابع والعشرين": [27],
            "تمت الاجزاء 2 و 5 و 9": [2, 5, 9],
            "كلمات عشوائية بدون ارقام": []
        }
        
        for text, expected_numbers in test_cases.items():
            with self.subTest(text=text):
                result = utilities.extract_arabic_numbers(text)
                self.assertEqual(result, expected_numbers)

if __name__ == '__main__':
    unittest.main(verbosity=2)