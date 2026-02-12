from enum import Enum

class Chapter:    
    class status(Enum):
        EMPTY = 0
        RESERVED = 1
        FINISHED = 2

    def __init__(self,khetma_id, number, owner, status=status.EMPTY):
        khetma_id = khetma_id
        number = number
        owner = owner
        status = status