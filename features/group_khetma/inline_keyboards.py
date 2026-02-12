from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from enum import Enum

class ButtonState(Enum):
    EMPTY = 0
    RESERVED = 1
    FINISHED = 2

def create_khetma_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    button_number = 1

    for row in range(6):
        row_buttons = []
        for col in range(5):
            row_buttons.append(InlineKeyboardButton(str(button_number), callback_data=f"callback_chapter{button_number}"))
            button_number += 1
        keyboard.append(row_buttons)

    return InlineKeyboardMarkup(keyboard)

def update_button_state(reply_markup: InlineKeyboardMarkup, callback_data, new_state=None) -> InlineKeyboardMarkup:
    # 1. Extract the number from string (e.g., "callback_chapter12" -> 12)
    try:
        button_number = str(callback_data).replace("callback_chapter", "")
        idx = int(button_number) - 1  # Shift to 0-based index
    except ValueError:
        return reply_markup # Handle unexpected callback data

    # 2. Direct Coordinate Math
    row = idx // 5
    col = idx % 5

    # 3. Access the button directly
    try:
        button = reply_markup.inline_keyboard[row][col]
    except IndexError:
        return reply_markup # Safety check if index is out of bounds

    # 4. Update the text
    if new_state == ButtonState.EMPTY:
        button.text = str(idx + 1)
    elif new_state == ButtonState.RESERVED:
        button.text = "⬜"
    elif new_state == ButtonState.FINISHED:
        button.text = "✅"

    return reply_markup

