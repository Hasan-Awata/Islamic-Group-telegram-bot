from telegram import  Update
from telegram import  error as TelegramError
from telegram.ext import ContextTypes

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
        await update.message.reply_text(errors.NotAdminError().message)
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
    except TelegramError.BadRequest as err:
        pass

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=command_message.message_id)
    except TelegramError.BadRequest as err:
        pass

async def finish_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    if not ({"تم", "تمت"} & set(message_text.split())):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    username = await utilities.get_username(chat_id, user.id, context)
    user_message = update.message
    reply_text = ""
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    # Extracted duplicated chapter-loop into one inner helper
    def _build_finish_reply(finished_chapters, get_khetma_num) -> str:
        text = ""
        for chapter in finished_chapters:
            text += responses.TEXT_TEMPLATES["finish_chapter_body"].format(
                chapter_num=chapter.number,
                khetma_num=get_khetma_num(chapter)
            ) + "\n"
        text += responses.TEXT_TEMPLATES["finish_chapter_footer"]
        return text

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

        if any(word in message_text.split() for word in ["أجزائي", "اجزائي"]):
            try:
                finished_chapters = storage.finish_all_user_chapters(chat_id, user.id, khetma_obj.khetma_id)
                # Using the helper function
                reply_text = _build_finish_reply(
                    finished_chapters,
                    get_khetma_num=lambda ch: khetma_obj.number
                )
            except (errors.DatabaseConnectionError, errors.NoOwnedChapters) as err:
                reply_text = err.message
        else:
            chapters = utilities.extract_arabic_numbers(message_text)
            if not chapters:
                reply_text = errors.NoOwnedChapters().message
            else:
                for chapter_num in chapters:
                    try:
                        if storage.finish_chapter(khetma_obj.khetma_id, int(chapter_num), user.id, username):
                            reply_text += responses.TEXT_TEMPLATES["finish_chapter_body"].format(
                                chapter_num=chapter_num,
                                khetma_num=khetma_obj.number
                            ) + "\n"
                    except (errors.DatabaseConnectionError, errors.ChapterFinishedError, errors.ChapterNotOwnedError) as err:
                        reply_text += err.message + "\n"
                reply_text += responses.TEXT_TEMPLATES["finish_chapter_footer"]

        # UI REFRESH
        updated_khetma = storage.get_khetma(khetma_id=khetma_obj.khetma_id)
        new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
        await user_message.reply_to_message.edit_text(
            text=utilities.create_khetma_message(updated_khetma),
            reply_markup=new_keyboard,
            parse_mode="Markdown"
        )

    else:
        if any(word in message_text.split() for word in ["أجزائي", "اجزائي"]):
            try:
                finished_chapters = storage.finish_all_user_chapters(chat_id, user.id)
                khetma_ids = list({ch.parent_khetma for ch in finished_chapters})
                khetma_cache = storage.get_khetmat_by_ids(khetma_ids)
                reply_text = _build_finish_reply(
                    finished_chapters,
                    get_khetma_num=lambda ch: khetma_cache[ch.parent_khetma]
                )
            except (errors.DatabaseConnectionError, errors.NoOwnedChapters) as err:
                reply_text = err.message
    if reply_text:
        await update.message.reply_text(reply_text)

async def handle_khetma_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = update.effective_chat.id

    callback_data = query.data.split("_")
    khetma_id = int(callback_data[1])
    chapter_number = int(callback_data[2])

    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    # Fetch the chapter first to check its state
    chapter = storage.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)
    if not chapter:
        await query.answer(errors.KhetmaNotFoundError().message, show_alert=True)
        return

    if chapter.is_reserved:
        # Just show who reserved it, do nothing else
        await query.answer(f"الجزء {chapter_number} محجوز بواسطة {chapter.owner_username}", show_alert=False)
        return

    # Otherwise proceed with reservation as normal
    try:
        storage.reserve_chapter(khetma_id, chapter_number, user.id, await utilities.get_username(chat_id, user.id, context))
    except (errors.ChapterAlreadyReservedError, errors.ChapterFinishedError) as e:
        await query.answer(e.message, show_alert=True)
        return

    updated_khetma = storage.get_khetma(khetma_id)
    new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
    await query.edit_message_text(
        text=utilities.create_khetma_message(updated_khetma),
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )
    await query.answer()


