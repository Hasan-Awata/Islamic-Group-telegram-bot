from enum import Enum
from typing import List, Dict, Any

# project modules
from class_chapter import Chapter 

class Khetma:
    class khetma_status(Enum):
        ACTIVE = "ACTIVE"
        FINISHED = "FINISHED"
    
    def __init__(self, khetma_id, number, status=khetma_status.ACTIVE, chapters: list[Chapter]=None):
        self.khetma_id = khetma_id
        self.number = number
        self.status = status
        if chapters:
            self.chapters = chapters
        else:
            self.chapters = [Chapter(chapter_num, None, Chapter.chapter_status.EMPTY) for chapter_num in range(1, 31)] 

    @property
    def is_finished(self):
        return len(self.get_reserved_chapters()) == 30
    
    def get_chapter(self, chapter_num) -> Chapter | None:
        if 1 <= chapter_num <= 30:
            return self.chapters[chapter_num - 1]
        return None
            
    def get_reserved_chapters(self) -> list[Chapter]:
        reserved_chapters = []
        for chapter in self.chapters:
            if chapter.is_reserved:
                reserved_chapters.append(chapter)
        
        return reserved_chapters

    def get_finished_chapters(self) -> list[Chapter]:
        finished_chapters = []
        for chapter in self.chapters:
            if chapter.is_finished:
                finished_chapters.append(chapter)
        
        return finished_chapters
    
    def get_available_chapters(self) -> list[Chapter]:
        available_chapters = []
        for chapter in self.chapters:
            if chapter.is_available:
                available_chapters.append(chapter)

        return available_chapters
    
    def reserve_chapter(self, user_id, username, chapter_num) -> bool:
        chapter = self.get_chapter(chapter_num)
        if not chapter.is_available:
            return False
        chapter.reserve(user_id, username)
    
    def mark_chapter_finished(self, chapter_num, user_id=None, username=None) -> bool:
        chapter = self.get_chapter(chapter_num)
        if chapter.is_finished:
            return False
        
        if chapter.is_available:
            chapter.owner_id = user_id
            chapter.owner_username = username

        chapter.mark_finished()
        return True

    def mark_chapter_empty(self, chapter_num) -> bool:
        chapter = self.get_chapter(chapter_num)
        if chapter.is_available:
            return False
        chapter.mark_empty()

    @classmethod
    def from_db_row(cls, khetma_row, chapters_rows) -> 'Khetma':
        """Factory: Converts a DB row + List of Chapter rows into a Khetma object."""
        return cls(
            khetma_id=khetma_row["khetma_id"],
            number=khetma_row["number"],
            status=cls.khetma_status[khetma_row["status"].upper()],
            chapters=[Chapter.from_db_row(row) for row in chapters_rows]
        )
    