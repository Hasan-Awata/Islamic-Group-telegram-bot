from enum import Enum
from typing import List, Dict, Any

# project modules
from class_chapter import Chapter 

class Khetma:
    class khetma_status(Enum):
        ACTIVE = "ACTIVE"
        FINISHED = "FINISHED"
    
    def __init__(self, khetma_id, number, status=khetma_status.ACTIVE):
        self.khetma_id = khetma_id
        self.number = number
        self.status = status
        self.chapters = [Chapter(chapter_num, None, Chapter.chapter_status.EMPTY) for chapter_num in range(1, 31)] 

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
    def from_dict(cls, khetma_dict: Dict[str, Any]) -> Khetma:
        """
        Pure Factory Method: Converts a raw dictionary into Khetma Object.
        """
        # Give me the next key value from the iteration over chapters dictionary
        # which is one value (the key) since I'm only fetching one chapter dictionary at a time
        khetma_id = next(iter(khetma_dict))

        khetma = Khetma(
            int(khetma_id),
            khetma_dict[khetma_id]["number"],
            cls.khetma_status[khetma_dict[khetma_id]["status"].upper()]
        )

        for chapter in khetma.chapters:
            chapter_number = str(chapter.number)

            if chapter_number in khetma_dict[khetma_id]["empty_chapters"]:
                chapter.mark_empty()
            elif chapter_number in khetma_dict[khetma_id]["reserved_chapters"]:
                chapter.reserve(khetma_dict[khetma_id]["reserved_chapters"][chapter_number])
            elif chapter_number in khetma_dict[khetma_id]["finished_chapters"]:
                chapter.mark_finished()

        return khetma

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Khetma object into a dictionary for database storage..
        """
        reserved_map = {}
        for chapter in self.get_reserved_chapters():
            reserved_map.update(chapter.to_dict())

        finished_map = {}
        for chapter in self.get_finished_chapters():
            finished_map.update(chapter.to_dict())

        return {
            self.khetma_id:{
            "number": self.number,
            "status": self.status.value,
            "empty_chapters": [chapter.number for chapter in self.get_available_chapters()],
            "reserved_chapters": reserved_map,
            "finished_chapters": finished_map,
            }
        }