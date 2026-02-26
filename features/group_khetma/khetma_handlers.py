from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatMember, Message
from telegram.ext import ContextTypes
import asyncio

# Local modules
import features.group_khetma.utilities as utilities
import features.group_khetma.inline_keyboards as inline_keyboards
import features.group_khetma.responses as responses
import features.group_khetma.errors as errors
from features.group_khetma.khetma_storage import KhetmaStorage

async def start_khetma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    command_message = update.message

    # 1. ADMIN CHECK
    if not await utilities.is_user_admin(chat_id, user_id, context):
        err_msg = await update.message.reply_text(responses.MESSAGE_BUILDERS["permession_denied"])
        await asyncio.sleep(5)
        try:
            await err_msg.delete()
        except Exception:
            pass
        return
        
    storage : KhetmaStorage = context.bot_data["khetma_storage"]

    khetma = storage.create_new_khetma(chat_id)

    khetma_message = await context.bot.send_message(
        chat_id=chat_id,
        text=responses.MESSAGE_BUILDERS["new_khetma"](khetma),
        reply_markup= inline_keyboards.render_khetma_keyboard(khetma),
        parse_mode='Markdown'
        )

    try:
        await context.bot.pin_chat_message(chat_id=chat_id, message_id=khetma_message.message_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=command_message.message_id)
    except Exception:
        pass

async def finish_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "تم" in update.message.text.split() or "تمت" in update.message.text.split():
        chat_id = update.effective_chat.id
        user = update.effective_user
        username = await utilities.get_username(chat_id, user.id, context)
        user_message = update.message
        reply_text = ""

        storage: KhetmaStorage = context.bot_data["khetma_storage"]

        if user_message.reply_to_message:
            numbers_in_text = utilities.extract_arabic_numbers(user_message.reply_to_message.text)

            if not numbers_in_text: 
                await user_message.reply_text(errors.KhetmaNotFoundError().message)
                return
            
            khetma_num = numbers_in_text[0]

            khetma_obj = storage.get_khetma(khetma_number=khetma_num, chat_id=chat_id)
            if not khetma_obj: 
                await user_message.reply_text(errors.KhetmaNotFoundError().message)
                return

            if any(word in user_message.text.split() for word in ["أجزائي", "اجزائي"]):
                try:
                    successful, failed =  storage.finish_all_user_chapters(user.id, username, khetma_obj.khetma_id)
                    
                    for chapter in successful:
                        reply_text += responses.TEXT_TEMPLATES["finish_chapter_body"].format(
                        chapter_num = chapter.number,
                        khetma_num = khetma_obj.number
                    ) + "\n"

                    for chapter, error in failed:
                        reply_text += responses.TEXT_TEMPLATES["finish_chapter_error"].format(
                        chapter_num = chapter.number,
                        khetma_num = khetma_obj.number,
                        error_message = error.message
                    ) + "\n"

                    reply_text += responses.TEXT_TEMPLATES["finish_chapter_footer"] if reply_text != "" else "ليس لديك أي أجزاء"
                except (errors.DatabaseConnectionError, errors.NoOwnedChapters) as err:
                    reply_text = err.message
            else:
                chapters = utilities.extract_arabic_numbers(user_message.text)
                if chapters == []:
                    reply_text = errors.NoOwnedChapters().message
                for chapter_num in chapters:
                    try:
                        if storage.finish_chapter(khetma_obj.khetma_id, int(chapter_num), user.id, username):
                            reply_text += responses.TEXT_TEMPLATES["finish_chapter_body"].format(
                                chapter_num = chapter_num,
                                khetma_num = khetma_obj.number 
                            ) + "\n"
                    except (errors.DatabaseConnectionError, errors.ChapterFinishedError, errors.ChapterNotOwnedError) as err:
                        reply_text += err.message + "\n"
                reply_text += responses.TEXT_TEMPLATES["finish_chapter_footer"]

            # ==========================================
            # UI REFRESH: Update the inline keyboard grid
            # ==========================================
            try:
                # 1. Fetch the fresh Khetma state from the database
                updated_khetma = storage.get_khetma(khetma_id=khetma_obj.khetma_id)
                
                # 2. Render the new keyboard using your existing function
                new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
                
                # 3. Edit the original message to show the new checkmarks
                await user_message.reply_to_message.edit_reply_markup(reply_markup=new_keyboard)
            except Exception as e:
                # If Telegram complains (e.g., the keyboard didn't actually change), ignore it
                pass
        else:
            if any(word in user_message.text.split() for word in ["أجزائي", "اجزائي"]):
                try:
                    successful, failed =  storage.finish_all_user_chapters(user.id, username)
                    
                    for chapter in successful:
                        reply_text += responses.TEXT_TEMPLATES["finish_chapter_body"].format(
                        chapter_num = chapter.number,
                        khetma_num = storage.get_khetma(chapter.parent_khetma).number
                    ) + "\n"

                    for chapter, error in failed:
                        reply_text += responses.TEXT_TEMPLATES["finish_chapter_error"].format(
                        chapter_num = chapter.number,
                        khetma_num = storage.get_khetma(chapter.parent_khetma).number,
                        error_message = error.message
                    ) + "\n"

                    reply_text += responses.TEXT_TEMPLATES["finish_chapter_footer"] if reply_text != "" else "ليس لديك أي أجزاء"
                except (errors.DatabaseConnectionError, errors.NoOwnedChapters) as err:
                    reply_text = err.message

        if reply_text != "":
            await update.message.reply_text(reply_text)

async def handle_button_reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = update.effective_chat.id

    callback_data = query.data.split("_")
    action = callback_data[0]
    khetma_id = callback_data[1]
    chapter_number = callback_data[2]

    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    if action == "reserve":
        try:
            storage.reserve_chapter(khetma_id, chapter_number, user.id, await utilities.get_username(chat_id, user.id, context))
        except (errors.ChapterAlreadyReservedError, errors.ChapterFinishedError) as e:
            await query.answer(e.message, show_alert=True)
            return
        try:
            updated_khetma = storage.get_khetma(khetma_id)
            new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
            await query.edit_message_text(text=utilities.create_khetma_message(updated_khetma),reply_markup=new_keyboard)
            await query.answer() 
        except Exception:
            pass


