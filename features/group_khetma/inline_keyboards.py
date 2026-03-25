from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Local modules
from features.group_khetma.class_khetma import Khetma

def render_khetma_keyboard(khetma: Khetma):
    """
    Generates a fixed 6x5 grid for the 30 Juz.
    """
    keyboard = []
    row = []

    for chapter in khetma.chapters:          
        
        # 1. Determine Text & Action
        if chapter.status.name == "FINISHED": # Use .name if Enum
            text = "✅"
            callback_data = f"info_{khetma.khetma_id}_{chapter.number}"
        
        elif chapter.status.name == "RESERVED":
            text = "⬜"
            # We keep the callback so if they click, we can say "Reserved by X"
            callback_data = f"info_{khetma.khetma_id}_{chapter.number}"
        
        else: # AVAILABLE
            text = str(chapter.number)
            callback_data = f"reserve_{khetma.khetma_id}_{chapter.number}"

        # 2. Add Button
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        
        # 3. Batch into rows of 5
        if len(row) == 5:
            keyboard.append(row)
            row = [] 
    
    keyboard.append([
        InlineKeyboardButton(
            text="قرأت جميع أجزائي ✅",
            callback_data=f"finish_all_{khetma.khetma_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text="أجزائي 📋",
            callback_data=f"my_chapters_{khetma.khetma_id}"
        ),
        InlineKeyboardButton(
            text="سحب أجزائي 🔄",
            callback_data=f"withdraw_all_{khetma.khetma_id}"
        )
    ])
        
    return InlineKeyboardMarkup(keyboard)