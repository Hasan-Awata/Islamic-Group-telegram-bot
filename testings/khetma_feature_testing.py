import unittest
from decouple import config
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Local imports
from storage_manager import StorageManager
from features.group_khetma.khetma_storage import KhetmaStorage
from features.group_khetma import errors
from features.group_khetma import utilities
from features.group_khetma.class_khetma import Khetma
from features.group_khetma.class_chapter import Chapter

# python -m unittest -v testings.khetma_feature_testing

# ==========================================
# TEST DATABASE SETUP
# Requires TEST_DATABASE_URL in your .env:
# TEST_DATABASE_URL=postgresql://user:password@localhost:5432/dullani_bot_test
# ==========================================

class TestStorageManager(StorageManager):
    """
    A StorageManager subclass that connects to the TEST database
    and wipes it clean before each test class run.
    """
    def __init__(self):
        self.dsn = config("TEST_DATABASE_URL")
        self.pool = pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=5,
            dsn=self.dsn,
            cursor_factory=RealDictCursor
        )
        self._drop_all_tables()
        self._init_chats_table()

    def _drop_all_tables(self):
        """Wipes the test database completely before each test."""
        with self.managed_connection() as cursor:
            cursor.execute("DROP TABLE IF EXISTS chapters CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS khetmat CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS chats CASCADE;")


# ==========================================
# TEST CLASS
# ==========================================

class TestGroupKhetma(unittest.TestCase):

    def setUp(self):
        """Runs before EVERY test. Creates a fresh database and storage."""
        self.db_core = TestStorageManager()
        self.storage = KhetmaStorage(self.db_core)

        # Fake Telegram Data
        self.chat_id = -100123456
        self.chat_id_b = -100999999  # A second independent chat
        self.user_a = {"id": 222, "username": "@UserA"}
        self.user_b = {"id": 333, "username": "@UserB"}
        self.user_c = {"id": 444, "username": "@UserC"}

    def tearDown(self):
        """Runs after EVERY test. Closes all pool connections."""
        self.db_core.pool.closeall()


    # ==========================================
    # 1. KHETMA CREATION TESTS
    # ==========================================

    def test_create_first_khetma(self):
        """A new khetma should be number 1, ACTIVE, with exactly 30 empty chapters."""
        khetma = self.storage.create_new_khetma(self.chat_id)

        self.assertEqual(khetma.number, 1)
        self.assertEqual(khetma.status, Khetma.khetma_status.ACTIVE)
        self.assertEqual(len(khetma.chapters), 30)
        self.assertTrue(all(ch.is_available for ch in khetma.chapters))

    def test_create_sequential_khetmas(self):
        """Each new khetma in the same chat should get an incrementing number."""
        khetma1 = self.storage.create_new_khetma(self.chat_id)
        khetma2 = self.storage.create_new_khetma(self.chat_id)
        khetma3 = self.storage.create_new_khetma(self.chat_id)

        self.assertEqual(khetma1.number, 1)
        self.assertEqual(khetma2.number, 2)
        self.assertEqual(khetma3.number, 3)

    def test_khetmas_are_independent_across_chats(self):
        """Khetmas in different chats should each start from number 1."""
        khetma_chat_a = self.storage.create_new_khetma(self.chat_id)
        khetma_chat_b = self.storage.create_new_khetma(self.chat_id_b)

        self.assertEqual(khetma_chat_a.number, 1)
        self.assertEqual(khetma_chat_b.number, 1)

    def test_chapters_are_numbered_1_to_30(self):
        """Chapters should be numbered 1 through 30 in order."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        chapter_numbers = [ch.number for ch in khetma.chapters]

        self.assertEqual(chapter_numbers, list(range(1, 31)))

    def test_get_khetma_by_id(self):
        """Fetching a khetma by its ID should return the correct khetma."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        fetched = self.storage.get_khetma(khetma_id=khetma.khetma_id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.khetma_id, khetma.khetma_id)
        self.assertEqual(fetched.number, 1)

    def test_get_khetma_by_number_and_chat(self):
        """Fetching a khetma by number + chat_id should return the correct one."""
        self.storage.create_new_khetma(self.chat_id)
        self.storage.create_new_khetma(self.chat_id)
        fetched = self.storage.get_khetma(khetma_number=2, chat_id=self.chat_id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.number, 2)

    def test_get_khetma_nonexistent_returns_none(self):
        """Fetching a khetma that doesn't exist should return None."""
        result = self.storage.get_khetma(khetma_id=99999)
        self.assertIsNone(result)

    def test_get_khetma_wrong_chat_returns_none(self):
        """Fetching khetma number 1 from the wrong chat should return None."""
        self.storage.create_new_khetma(self.chat_id)
        result = self.storage.get_khetma(khetma_number=1, chat_id=self.chat_id_b)
        self.assertIsNone(result)


    # ==========================================
    # 2. RESERVATION TESTS
    # ==========================================

    def test_reserve_chapter_success(self):
        """A user should be able to reserve an available chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        result = self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.assertTrue(result)

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        self.assertTrue(chapter.is_reserved)
        self.assertEqual(chapter.owner_id, self.user_a["id"])
        self.assertEqual(chapter.owner_username, self.user_a["username"])

    def test_reserve_chapter_persists_to_db(self):
        """A reserved chapter fetched fresh from DB should still show as reserved."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )

        # Re-fetch the full khetma from DB
        refreshed = self.storage.get_khetma(khetma_id=khetma.khetma_id)
        chapter_5 = refreshed.get_chapter(5)

        self.assertTrue(chapter_5.is_reserved)
        self.assertEqual(chapter_5.owner_username, self.user_a["username"])

    def test_reserve_already_reserved_chapter_raises_error(self):
        """Trying to reserve a chapter someone else already took should raise ChapterAlreadyReservedError."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterAlreadyReservedError):
            self.storage.reserve_chapter(
                khetma.khetma_id, 1, self.user_b["id"], self.user_b["username"]
            )

    def test_reserve_finished_chapter_raises_error(self):
        """Trying to reserve a chapter that is already finished should raise ChapterFinishedError."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterFinishedError):
            self.storage.reserve_chapter(
                khetma.khetma_id, 1, self.user_b["id"], self.user_b["username"]
            )

    def test_same_user_can_reserve_multiple_chapters(self):
        """A user should be able to reserve more than one chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 2, self.user_a["id"], self.user_a["username"]
        )

        ch1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        ch2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)

        self.assertTrue(ch1.is_reserved)
        self.assertTrue(ch2.is_reserved)
        self.assertEqual(ch1.owner_id, self.user_a["id"])
        self.assertEqual(ch2.owner_id, self.user_a["id"])

    def test_multiple_users_reserve_different_chapters(self):
        """Multiple users should each be able to reserve different chapters."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 10, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 20, self.user_b["id"], self.user_b["username"]
        )

        ch10 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=10)
        ch20 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=20)

        self.assertEqual(ch10.owner_id, self.user_a["id"])
        self.assertEqual(ch20.owner_id, self.user_b["id"])


    # ==========================================
    # 3. WITHDRAW TESTS
    # ==========================================

    def test_withdraw_chapter_success(self):
        """A user should be able to withdraw their own reserved chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 10, self.user_a["id"], self.user_a["username"]
        )
        self.storage.withdraw_chapter(khetma.khetma_id, 10, self.user_a["id"])

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=10)
        self.assertTrue(chapter.is_available)
        self.assertIsNone(chapter.owner_id)
        self.assertIsNone(chapter.owner_username)

    def test_withdraw_clears_owner_data(self):
        """Withdrawing a chapter should clear the owner_id and owner_username."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 3, self.user_a["id"], self.user_a["username"]
        )
        self.storage.withdraw_chapter(khetma.khetma_id, 3, self.user_a["id"])

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=3)
        self.assertIsNone(chapter.owner_id)
        self.assertIsNone(chapter.owner_username)

    def test_withdraw_allows_rerservation(self):
        """After withdrawing, another user should be able to reserve that chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 7, self.user_a["id"], self.user_a["username"]
        )
        self.storage.withdraw_chapter(khetma.khetma_id, 7, self.user_a["id"])
        self.storage.reserve_chapter(
            khetma.khetma_id, 7, self.user_b["id"], self.user_b["username"]
        )

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=7)
        self.assertTrue(chapter.is_reserved)
        self.assertEqual(chapter.owner_id, self.user_b["id"])

    def test_withdraw_someone_elses_chapter_raises_error(self):
        """A user should not be able to withdraw a chapter reserved by someone else."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterNotOwnedError):
            self.storage.withdraw_chapter(khetma.khetma_id, 1, self.user_b["id"])

    def test_withdraw_empty_chapter_raises_error(self):
        """Trying to withdraw a chapter that is not reserved should raise ChapterAlreadyEmptyError."""
        khetma = self.storage.create_new_khetma(self.chat_id)

        with self.assertRaises(errors.ChapterAlreadyEmptyError):
            self.storage.withdraw_chapter(khetma.khetma_id, 1, self.user_a["id"])

    def test_withdraw_finished_chapter_raises_error(self):
        """Trying to withdraw a finished chapter should raise ChapterFinishedError."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterFinishedError):
            self.storage.withdraw_chapter(khetma.khetma_id, 1, self.user_a["id"])

    def test_admin_can_withdraw_any_chapter(self):
        """An admin should be able to withdraw a chapter regardless of ownership."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 15, self.user_a["id"], self.user_a["username"]
        )
        self.storage.withdraw_chapter(
            khetma.khetma_id, 15, self.user_b["id"], is_admin=True
        )

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=15)
        self.assertTrue(chapter.is_available)


    # ==========================================
    # 4. FINISH CHAPTER TESTS
    # ==========================================

    def test_finish_reserved_chapter_success(self):
        """The owner of a reserved chapter should be able to finish it."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )
        result = self.storage.finish_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )
        self.assertTrue(result)

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=5)
        self.assertTrue(chapter.is_finished)

    def test_finish_chapter_preserves_owner(self):
        """Finishing a chapter should preserve the owner's data."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=5)
        self.assertEqual(chapter.owner_id, self.user_a["id"])
        self.assertEqual(chapter.owner_username, self.user_a["username"])

    def test_finish_chapter_not_owned_raises_error(self):
        """A user should not be able to finish a chapter reserved by someone else."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterNotOwnedError):
            self.storage.finish_chapter(
                khetma.khetma_id, 5, self.user_b["id"], self.user_b["username"]
            )

    def test_finish_already_finished_chapter_raises_error(self):
        """Finishing an already finished chapter should raise ChapterFinishedError."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_chapter(
            khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )

        with self.assertRaises(errors.ChapterFinishedError):
            self.storage.finish_chapter(
                khetma.khetma_id, 5, self.user_a["id"], self.user_a["username"]
            )

    def test_finish_empty_chapter_assigns_to_finisher(self):
        """
        Finishing an unreserved (EMPTY) chapter should assign it to the
        user who finished it — this is an edge case allowed by the SQL logic.
        """
        khetma = self.storage.create_new_khetma(self.chat_id)
        result = self.storage.finish_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.assertTrue(result)

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        self.assertTrue(chapter.is_finished)
        self.assertEqual(chapter.owner_id, self.user_a["id"])


    # ==========================================
    # 5. FINISH ALL USER CHAPTERS TESTS
    # ==========================================

    def test_finish_all_user_chapters_in_specific_khetma(self):
        """finish_all_user_chapters with khetma_id should only finish chapters in that khetma."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 2, self.user_a["id"], self.user_a["username"]
        )

        finished = self.storage.finish_all_user_chapters(
            self.chat_id, self.user_a["id"], khetma.khetma_id
        )
        self.assertEqual(len(finished), 2)

        ch1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        ch2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)
        self.assertTrue(ch1.is_finished)
        self.assertTrue(ch2.is_finished)

    def test_finish_all_user_chapters_across_all_khetmas_in_chat(self):
        """finish_all_user_chapters without khetma_id should finish all chapters across the chat."""
        khetma1 = self.storage.create_new_khetma(self.chat_id)
        khetma2 = self.storage.create_new_khetma(self.chat_id)

        self.storage.reserve_chapter(
            khetma1.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma2.khetma_id, 5, self.user_a["id"], self.user_a["username"]
        )

        finished = self.storage.finish_all_user_chapters(self.chat_id, self.user_a["id"])
        self.assertEqual(len(finished), 2)

    def test_finish_all_chapters_does_not_affect_other_users(self):
        """finish_all_user_chapters should only finish chapters owned by the specified user."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 2, self.user_b["id"], self.user_b["username"]
        )

        self.storage.finish_all_user_chapters(
            self.chat_id, self.user_a["id"], khetma.khetma_id
        )

        ch1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        ch2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)
        self.assertTrue(ch1.is_finished)
        self.assertTrue(ch2.is_reserved)  # User B's chapter untouched

    def test_finish_all_chapters_does_not_cross_chat_boundaries(self):
        """finish_all_user_chapters should not touch chapters in a different chat."""
        khetma_a = self.storage.create_new_khetma(self.chat_id)
        khetma_b = self.storage.create_new_khetma(self.chat_id_b)

        self.storage.reserve_chapter(
            khetma_a.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma_b.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        # Only finish for chat_id, not chat_id_b
        finished = self.storage.finish_all_user_chapters(self.chat_id, self.user_a["id"])
        self.assertEqual(len(finished), 1)

        # Chapter in the other chat should still be reserved
        ch_other = self.storage.get_chapter(
            khetma_id=khetma_b.khetma_id, chapter_number=1
        )
        self.assertTrue(ch_other.is_reserved)

    def test_finish_all_user_chapters_no_chapters_raises_error(self):
        """finish_all_user_chapters with no reserved chapters should raise NoOwnedChapters."""
        self.storage.create_new_khetma(self.chat_id)

        with self.assertRaises(errors.NoOwnedChapters):
            self.storage.finish_all_user_chapters(self.chat_id, self.user_a["id"])

    def test_finish_all_chapters_twice_raises_error_second_time(self):
        """Calling finish_all_user_chapters again after all are done should raise NoOwnedChapters."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_all_user_chapters(self.chat_id, self.user_a["id"])

        with self.assertRaises(errors.NoOwnedChapters):
            self.storage.finish_all_user_chapters(self.chat_id, self.user_a["id"])


    # ==========================================
    # 6. GET CHAPTERS BY USER TESTS
    # ==========================================

    def test_get_chapters_by_user(self):
        """get_chapters_by_user should return all chapters owned by a user."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 2, self.user_a["id"], self.user_a["username"]
        )

        chapters = self.storage.get_chapters_by_user(self.user_a["id"])
        self.assertEqual(len(chapters), 2)
        self.assertTrue(all(ch.owner_id == self.user_a["id"] for ch in chapters))

    def test_get_chapters_by_user_with_khetma_filter(self):
        """get_chapters_by_user with khetma_id should only return chapters from that khetma."""
        khetma1 = self.storage.create_new_khetma(self.chat_id)
        khetma2 = self.storage.create_new_khetma(self.chat_id)

        self.storage.reserve_chapter(
            khetma1.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma2.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        chapters = self.storage.get_chapters_by_user(
            self.user_a["id"], khetma_id=khetma1.khetma_id
        )
        self.assertEqual(len(chapters), 1)
        self.assertEqual(chapters[0].parent_khetma, khetma1.khetma_id)

    def test_get_chapters_by_user_no_chapters_raises_error(self):
        """get_chapters_by_user for a user with no chapters should raise NoOwnedChapters."""
        self.storage.create_new_khetma(self.chat_id)

        with self.assertRaises(errors.NoOwnedChapters):
            self.storage.get_chapters_by_user(self.user_a["id"])


    # ==========================================
    # 7. GET KHETMAT BY IDS TESTS
    # ==========================================

    def test_get_khetmat_by_ids(self):
        """get_khetmat_by_ids should return a dict mapping khetma_id to khetma number."""
        khetma1 = self.storage.create_new_khetma(self.chat_id)
        khetma2 = self.storage.create_new_khetma(self.chat_id)

        result = self.storage.get_khetmat_by_ids(
            [khetma1.khetma_id, khetma2.khetma_id]
        )

        self.assertEqual(result[khetma1.khetma_id], 1)
        self.assertEqual(result[khetma2.khetma_id], 2)

    def test_get_khetmat_by_ids_single(self):
        """get_khetmat_by_ids with a single ID should return a dict with one entry."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        result = self.storage.get_khetmat_by_ids([khetma.khetma_id])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[khetma.khetma_id], 1)


    # ==========================================
    # 8. CALC FUNCTIONS TESTS
    # ==========================================

    def test_calc_next_khetma_number_first(self):
        """calc_next_khetma_number for a chat with no khetmas should return 1."""
        result = self.storage.calc_next_khetma_number(self.chat_id)
        self.assertEqual(result, 1)

    def test_calc_next_khetma_number_after_creation(self):
        """calc_next_khetma_number should increment after each khetma is created."""
        self.storage.create_new_khetma(self.chat_id)
        self.storage.create_new_khetma(self.chat_id)
        result = self.storage.calc_next_khetma_number(self.chat_id)
        self.assertEqual(result, 3)

    def test_calc_finished_khetmat_number(self):
        """calc_finished_khetmat_number should count only FINISHED khetmas + 1."""
        self.storage.create_new_khetma(self.chat_id)
        khetma2 = self.storage.create_new_khetma(self.chat_id)

        # Manually mark khetma2 as FINISHED
        khetma2.status = Khetma.khetma_status.FINISHED
        self.storage.update_khetma(khetma2)

        result = self.storage.calc_finished_khetmat_number(self.chat_id)
        self.assertEqual(result, 2)  # 1 finished + 1


    # ==========================================
    # 9. KHETMA IS_FINISHED PROPERTY TESTS
    # ==========================================

    def test_khetma_is_not_finished_when_empty(self):
        """A freshly created khetma with no finished chapters should not be finished."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.assertFalse(khetma.is_finished)

    def test_khetma_is_finished_when_all_chapters_done(self):
        """A khetma where all 30 chapters are finished should report is_finished as True."""
        khetma = self.storage.create_new_khetma(self.chat_id)

        # Finish all 30 chapters as user_a
        for i in range(1, 31):
            self.storage.finish_chapter(
                khetma.khetma_id, i, self.user_a["id"], self.user_a["username"]
            )

        refreshed = self.storage.get_khetma(khetma_id=khetma.khetma_id)
        self.assertTrue(refreshed.is_finished)

    def test_khetma_is_not_finished_with_29_chapters_done(self):
        """A khetma with 29 finished chapters should not be considered finished."""
        khetma = self.storage.create_new_khetma(self.chat_id)

        for i in range(1, 30):  # Only 29
            self.storage.finish_chapter(
                khetma.khetma_id, i, self.user_a["id"], self.user_a["username"]
            )

        refreshed = self.storage.get_khetma(khetma_id=khetma.khetma_id)
        self.assertFalse(refreshed.is_finished)


    # ==========================================
    # 10. UPDATE METHODS TESTS
    # ==========================================

    def test_update_khetma_status(self):
        """update_khetma should persist status changes to the database."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        khetma.status = Khetma.khetma_status.FINISHED
        result = self.storage.update_khetma(khetma)
        self.assertTrue(result)

        refreshed = self.storage.get_khetma(khetma_id=khetma.khetma_id)
        self.assertEqual(refreshed.status, Khetma.khetma_status.FINISHED)

    def test_update_chapters_single(self):
        """update_chapters with a single Chapter object should update that chapter."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        chapter = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        chapter.status = Chapter.chapter_status.FINISHED
        self.storage.update_chapters(chapter)

        refreshed = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        self.assertTrue(refreshed.is_finished)

    def test_update_chapters_bulk(self):
        """update_chapters with a list of chapters should update all of them."""
        khetma = self.storage.create_new_khetma(self.chat_id)
        self.storage.reserve_chapter(
            khetma.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.reserve_chapter(
            khetma.khetma_id, 2, self.user_a["id"], self.user_a["username"]
        )

        ch1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        ch2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)
        ch1.status = Chapter.chapter_status.FINISHED
        ch2.status = Chapter.chapter_status.FINISHED
        self.storage.update_chapters([ch1, ch2])

        r1 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=1)
        r2 = self.storage.get_chapter(khetma_id=khetma.khetma_id, chapter_number=2)
        self.assertTrue(r1.is_finished)
        self.assertTrue(r2.is_finished)


    # ==========================================
    # 11. ARABIC NUMBER EXTRACTION TESTS
    # ==========================================

    def test_extract_arabic_numbers(self):
        """extract_arabic_numbers should handle all supported formats correctly."""
        test_cases = {
            "تم 1": [1],
            "تمت 30": [30],
            "تم الجزء الأول": [1],
            "تم 1 و 30": [1, 30],
            "الجزء الخامس و العشرون": [25],
            "قرأت السابع والعشرين": [27],
            "تمت الاجزاء 2 و 5 و 9": [2, 5, 9],
            "تم ١٥": [15],                          # Arabic-Indic digits
            "تم الجزء العاشر": [10],
            "تم الجزء الثلاثين": [30],
            "تم الحادي عشر": [11],
            "تم العشرون": [20],
            "كلمات عشوائية بدون ارقام": [],
        }

        for text, expected in test_cases.items():
            with self.subTest(text=text):
                result = utilities.extract_arabic_numbers(text)
                self.assertEqual(result, expected)

    def test_extract_multiple_numbers_ordered(self):
        """extract_arabic_numbers should return numbers in the order they appear."""
        result = utilities.extract_arabic_numbers("تمت الأجزاء 5 و 3 و 1")
        self.assertEqual(result, [5, 3, 1])

    def test_extract_numbers_with_mixed_formats(self):
        """extract_arabic_numbers should handle mixed digit formats in one string."""
        result = utilities.extract_arabic_numbers("تم 1 و الثاني و ٣")
        self.assertEqual(result, [1, 2, 3])


    # ==========================================
    # 12. MULTI-CHAT ISOLATION TESTS
    # ==========================================

    def test_operations_in_one_chat_dont_affect_another(self):
        """Reserving and finishing chapters in chat A should not affect chat B."""
        khetma_a = self.storage.create_new_khetma(self.chat_id)
        khetma_b = self.storage.create_new_khetma(self.chat_id_b)

        self.storage.reserve_chapter(
            khetma_a.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )
        self.storage.finish_chapter(
            khetma_a.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        ch_b = self.storage.get_chapter(
            khetma_id=khetma_b.khetma_id, chapter_number=1
        )
        self.assertTrue(ch_b.is_available)

    def test_user_chapters_scoped_to_chat(self):
        """A user's chapters in chat A should not appear when querying chat B."""
        khetma_a = self.storage.create_new_khetma(self.chat_id)
        self.storage.create_new_khetma(self.chat_id_b)

        self.storage.reserve_chapter(
            khetma_a.khetma_id, 1, self.user_a["id"], self.user_a["username"]
        )

        # finish_all for chat_id_b — user_a has no chapters there
        with self.assertRaises(errors.NoOwnedChapters):
            self.storage.finish_all_user_chapters(self.chat_id_b, self.user_a["id"])


if __name__ == '__main__':
    unittest.main(verbosity=2)