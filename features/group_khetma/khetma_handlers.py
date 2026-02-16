from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import asyncio

# Local modules
import utilities
from inline_keyboards import render_khetma_keyboard
from responses import RESPONSES
from khetma_storage import KhetmaStorage

async def start_khetma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    command_message_id = update.message.message_id 

    # 1. ADMIN CHECK
    if not await utilities.is_user_admin(chat_id, user_id, context):
        err_msg = update.message.reply_text(RESPONSES["permession_denied"])
        await asyncio.sleep(5)
        try:
            command_message_id.delete()
            err_msg.delete()
        except Exception:
            pass
        
    storage : KhetmaStorage = context.bot_data["khetma_storage"]

    khetma = storage.create_new_khetma(chat_id)

    khetma_message_id = await context.bot.send_message(
        chat_id=chat_id,
        text=RESPONSES["new_khetma"](khetma),
        reply_markup= render_khetma_keyboard(khetma),
        parse_mode='Markdown'
        )

    try:
        context.bot.pin_chat_message(chat_id=chat_id, message_id=khetma_message_id)
        context.bot.delete_message(chat_id=chat_id, message_id=command_message_id)
    except Exception:
        pass

async def messages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if "تم" in update.message.text.split() or "تمت" in update.message.text.split():
        if update.message.reply_to_message.message_id is None:
            await update.message.reply_text("الرجاء الرد على رسالة الختمة المقصودة")