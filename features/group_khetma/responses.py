# Local Imports
from class_khetma import Khetma
import utilities


MESSAGE_BUILDERS = {
    "new_khetma": utilities.create_khetma_message,
}

TEXT_TEMPLATES = {
    "finish_chapter_body": "لقد قرأت الجزء {chapter_num} من الختمة {khetma_num} ✅",
    "finish_chapter_footer": "جزاك الله خيراً 🤍",
    "finish_chapter_error": "بالنسبة للجزء {chapter_num} من الختمة {khetma_num}: {erro_message}"
}