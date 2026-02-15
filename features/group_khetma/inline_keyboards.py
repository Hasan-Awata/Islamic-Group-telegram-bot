from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Local modules
from class_khetma import Khetma
from class_chapter import Chapter

def render_khetma_keyboard(khetma: Khetma):
    """
    Generates the 5x6 grid based on the real time status of the Khetma object.
    """
    keyboard = []
    row = []

    for chapter in khetma.chapters:          
        if chapter.is_finished:
            text = "✅"
        elif chapter.is_reserved:
            text = "⬜"
        else:
            text = str(chapter.number)
        
        callback_data = f"reserve_{khetma.khetma_id}_{chapter.number}"

        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        
        if len(row) == 5:
            keyboard.append(row)
            row = []
    
    return InlineKeyboardMarkup(keyboard)
