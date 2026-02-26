from enum import Enum
from typing import Any

class Chapter:    
    class chapter_status(Enum):
        EMPTY = "EMPTY"
        RESERVED = "RESERVED"
        FINISHED = "FINISHED"

    def __init__(self, parent_khetma, number, owner_id, owner_username, status=chapter_status.EMPTY):
        self.parent_khetma = parent_khetma
        self.number = number
        self.owner_id = owner_id
        self.owner_username = owner_username
        self.status = status
    
    def reserve(self, owner_id, owner_username):
        self.status = self.chapter_status.RESERVED
        self.owner_id = owner_id
        self.owner_username = owner_username

    def mark_finished(self):
        self.status = self.chapter_status.FINISHED

    def mark_empty(self):
        self.status = self.chapter_status.EMPTY
        self.owner_id = None
        self.owner_username = None

    @property
    def is_available(self):
        return self.status == self.chapter_status.EMPTY

    @property
    def is_reserved(self):
        return self.status == self.chapter_status.RESERVED

    @property
    def is_finished(self):
        return self.status == self.chapter_status.FINISHED
    
    @classmethod
    def from_db_row(cls, row) -> 'Chapter':
        """Factory: Converts a DB row (sqlite3.Row) into a Chapter object."""
        return cls(
            parent_khetma=row["khetma_id"],
            number=row["number"],
            owner_id=row["owner_id"],
            owner_username=row["owner_username"], 
            status=cls.chapter_status[row["status"].upper()]
        )
    