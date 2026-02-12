from enum import Enum

# project modules
from class_chapter import Chapter 

class Khetma:
    class status(Enum):
        IN_PROGRESS = 0
        FINISHED = 1

    def __init__(self, khetma_id, number, status=status.IN_PROGRESS):
        self.khetma_id = khetma_id
        self.number = number
        self.status = status
        self.chapters = [Chapter(khetma_id, chapter, None) for chapter in range(1, 31)] 

    def get_empty_chapters(self) -> list:
        empty_chapters = []
        for chapter in self.chapters:
            if chapter.status.EMPTY:
                empty_chapters.append(chapter)
        
        return empty_chapters
    