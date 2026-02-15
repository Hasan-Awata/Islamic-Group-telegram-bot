# Local Imports
from class_khetma import Khetma
import utilities


RESPONSES = {
    "new_khetma": utilities.create_khetma_message,
    "permession_denied": "عذراً, يمكن للأدمن فقط إنشاء ختمات جديدة",
    "already_reserved": "عذراً {username}, ان الجزء {chapter_num} محجوز بالفعل.",
    "already_finished": "عذراً {username}, ان الجزء {chapter_num} منتهٍ بالفعل.",
}
