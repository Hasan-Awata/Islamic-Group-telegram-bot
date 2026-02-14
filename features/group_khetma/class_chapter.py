from enum import Enum
from typing import Any

class Chapter:    
    class chapter_status(Enum):
        EMPTY = "EMPTY"
        RESERVED = "RESERVED"
        FINISHED = "FINISHED"

    def __init__(self, number, owner, status=chapter_status.EMPTY):
        self.number = number
        self.owner = owner
        self.status = status
    
    def reserve(self, owner_id):
        self.status = self.chapter_status.RESERVED
        self.owner = owner_id

    def mark_finished(self):
        self.status = self.chapter_status.FINISHED

    def mark_empty(self):
        self.status = self.chapter_status.EMPTY
        self.owner = None

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
    def from_dict(cls, chapter_dict: dict[str, Any]) -> Chapter:
        
        # Give me the next key value from the iteration over chapters dictionary
        # which is one value (the key) since I'm only fetching one chapter dictionary at a time
        ch_num = next(iter(chapter_dict))
        
        chapter_obj = Chapter(
            int(ch_num),
            chapter_dict[ch_num]["owner"],
            cls.chapter_status[chapter_dict[ch_num]["status"].upper()]   
        )

        return chapter_obj

    def to_dict(self) -> dict[str, Any]:
        """
        Converts this object back to: {'1': {'owner': 12345, 'status': 'RESERVED'}}
        """
        return {
            str(self.number): {
                "owner": self.owner,
                "status": self.status.value 
            }
        }
