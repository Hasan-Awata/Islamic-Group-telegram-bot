from telegram import  Update
from telegram import  error as TelegramError
from telegram.ext import ContextTypes

# Local modules
import features.group_khetma.utilities as utilities
import features.group_khetma.inline_keyboards as inline_keyboards
import features.group_khetma.responses as responses
import features.group_khetma.errors as errors
from features.group_khetma.khetma_storage import KhetmaStorage
from features.group_khetma.class_khetma import Khetma

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

async def activate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not await utilities.is_user_admin(chat_id, user_id, context):
        await update.message.reply_text("🔒 عذراً، هذا الأمر متاح للمشرفين فقط.")
        return

    # Update Database
    storage = context.bot_data["khetma_storage"]
    storage.set_chat_active(chat_id, True)
    
    # Update RAM Cache instantly
    if "active_chats_cache" not in context.bot_data:
        context.bot_data["active_chats_cache"] = {}
    context.bot_data["active_chats_cache"][chat_id] = True

    await update.message.reply_text("✅ تم تفعيل البوت في هذه المجموعة بنجاح! يمكنكم الآن البدء.")

async def deactivate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if not await utilities.is_user_admin(chat_id, user_id, context):
        await update.message.reply_text("🔒 عذراً، هذا الأمر متاح للمشرفين فقط.")
        return

    # Update Database
    storage = context.bot_data["khetma_storage"]
    storage.set_chat_active(chat_id, False)
    
    # Update RAM Cache instantly
    if "active_chats_cache" not in context.bot_data:
        context.bot_data["active_chats_cache"] = {}
    context.bot_data["active_chats_cache"][chat_id] = False

    await update.message.reply_text("⏸️ تم إيقاف البوت في هذه المجموعة. لن يقوم بقراءة أي رسائل بعد الآن.")

async def finish_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    words = message_text.split()

    if not ({"تم", "تمت"} & set(words)):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    username = await utilities.get_username(chat_id, user.id, context)
    user_message = update.message
    reply_text = ""
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    if not user_message.reply_to_message:
        return

    numbers_in_text = utilities.extract_arabic_numbers(user_message.reply_to_message.text)
    if not numbers_in_text:
        await user_message.reply_text(errors.KhetmaNotFoundError().message)
        return

    khetma_num = numbers_in_text[0]
    khetma_obj = storage.get_khetma(khetma_number=khetma_num, chat_id=chat_id)
    if not khetma_obj:
        await user_message.reply_text(errors.KhetmaNotFoundError().message)
        return

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

    updated_khetma = storage.get_khetma(khetma_id=khetma_obj.khetma_id)
    new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
    await user_message.reply_to_message.edit_text(
        text=utilities.create_khetma_message(updated_khetma),
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )

    if updated_khetma.is_finished:
        updated_khetma.status = Khetma.khetma_status.FINISHED
        storage.update_khetma(updated_khetma)
        completed_khetma_text = responses.TEXT_TEMPLATES["completed_khetma"].format(khetma_num=updated_khetma.number)
        await user_message.reply_to_message.edit_text(
            text=utilities.create_khetma_message(updated_khetma),
            parse_mode="Markdown"
        )
        await context.bot.send_message(chat_id, completed_khetma_text, parse_mode="Markdown")

    if reply_text:
        await update.message.reply_text(reply_text)

async def my_chapters_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    words = set(message_text.split())

    if not ({"أجزائي", "اجزائي"} & words):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    try:
        chapters = storage.get_chapters_by_user(user.id, chat_id)
    except errors.NoOwnedChapters:
        await update.message.reply_text(errors.NoOwnedChapters().message)
        return

    # Group chapters by khetma
    khetma_ids = list({ch.parent_khetma for ch in chapters})
    khetma_cache = storage.get_khetmat_by_ids(khetma_ids)

    reply_text = ""
    for khetma_id, khetma_number in khetma_cache.items():
        khetma_chapters = [ch for ch in chapters if ch.parent_khetma == khetma_id]
        chapters_text = " و ".join(str(ch.number) for ch in khetma_chapters)
        reply_text += f"الختمة {khetma_number}: الجزء {chapters_text}\n"

    await update.message.reply_text(reply_text.strip())

async def available_chapters_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""

    if not (("أجزاء" in message_text or "اجزاء" in message_text) and "في" in message_text):
        return

    chat_id = update.effective_chat.id
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    khetmat = storage.get_active_khetmat(chat_id)
    if not khetmat:
        await update.message.reply_text("لا توجد ختمة نشطة في هذه المجموعة.")
        return

    reply_text = ""
    for khetma in khetmat:
        available = khetma.get_available_chapters()
        if not available:
            reply_text += f"الختمة {khetma.number}: لا توجد أجزاء متاحة\n"
        else:
            chapters_text = " و ".join(str(ch.number) for ch in available)
            reply_text += f"الختمة {khetma.number}: {chapters_text}\n"

    await update.message.reply_text(reply_text.strip())

async def admin_withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    words = set(message_text.split())

    if "سحب" not in words:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_message = update.message
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    if not await utilities.is_user_admin(chat_id, user_id, context):
        await user_message.reply_text(errors.NotAdminError().message)
        return

    if not user_message.reply_to_message:
        await user_message.reply_text("⚠️ الرجاء الرد على رسالة الختمة المقصودة.")
        return

    numbers_in_text = utilities.extract_arabic_numbers(user_message.reply_to_message.text)
    if not numbers_in_text:
        await user_message.reply_text(errors.KhetmaNotFoundError().message)
        return

    khetma_num = numbers_in_text[0]
    khetma_obj = storage.get_khetma(khetma_number=khetma_num, chat_id=chat_id)
    if not khetma_obj:
        await user_message.reply_text(errors.KhetmaNotFoundError().message)
        return

    chapters = utilities.extract_arabic_numbers(message_text)
    if not chapters:
        await user_message.reply_text(errors.NoOwnedChapters().message)
        return

    reply_text = ""
    action_happened = False
    for chapter_num in chapters:
        try:
            storage.withdraw_chapter(khetma_obj.khetma_id, int(chapter_num), user_id, is_admin=True)
            reply_text += f"✅ تم سحب الجزء {chapter_num} من الختمة {khetma_obj.number}\n"
            action_happened = True
        except (errors.ChapterAlreadyEmptyError, errors.DatabaseConnectionError, errors.ChapterFinishedError) as err:
            reply_text += f"{err.message}\n"

    if action_happened:
        updated_khetma = storage.get_khetma(khetma_id=khetma_obj.khetma_id)
        new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
        await user_message.reply_to_message.edit_text(
            text=utilities.create_khetma_message(updated_khetma),
            reply_markup=new_keyboard,
            parse_mode="Markdown"
        )

    if reply_text:
        await user_message.reply_text(reply_text.strip())

async def remind_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    words = set(message_text.split())

    if "تذكير" not in words:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    if not await utilities.is_user_admin(chat_id, user_id, context):
        await update.message.reply_text(errors.NotAdminError().message)
        return

    khetmat = storage.get_active_khetmat(chat_id)
    if not khetmat:
        await update.message.reply_text("لا توجد ختمة نشطة في هذه المجموعة.")
        return

    reply_text = ""
    for khetma in khetmat:
        reserved = khetma.get_reserved_chapters()
        if not reserved:
            continue

        reply_text += f"الختمة رقم {khetma.number}:\n"
        for chapter in reserved:
            username = await utilities.get_username(chat_id, chapter.owner_id, context)
            reply_text += f"• الجزء {chapter.number} ← {username}\n"
        reply_text += "\n"

    if not reply_text:
        await update.message.reply_text("✅ جميع الأجزاء المحجوزة تم إنهاؤها.")
        return

    header = "📢 تذكير بالأجزاء غير المكتملة:\n━━━━━━━━━━━━━━━━━━\n"
    await update.message.reply_text(header + reply_text.strip())


async def _handle_finish_all(query, user, chat_id, storage: KhetmaStorage, context):
    khetma_id = int(query.data.split("_")[2])
    try:
        finished_chapters = storage.finish_all_user_chapters(chat_id, user.id, khetma_id)
    except errors.NoOwnedChapters:
        await query.answer("لا يوجد أي أجزاء محجوزة باسمك ⛔", show_alert=True)
        return
    except errors.DatabaseConnectionError as e:
        await query.answer(e.message, show_alert=True)
        return

    chapters_text = " و ".join(str(ch.number) for ch in finished_chapters)
    await query.answer(f"تم إنهاء الأجزاء: {chapters_text} ✅", show_alert=True)

    updated_khetma = storage.get_khetma(khetma_id=khetma_id)
    new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
    await query.edit_message_text(
        text=utilities.create_khetma_message(updated_khetma),
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )

    if updated_khetma.is_finished:
        updated_khetma.status = Khetma.khetma_status.FINISHED
        storage.update_khetma(updated_khetma)
        completed_khetma_text = responses.TEXT_TEMPLATES["completed_khetma"].format(
            khetma_num=updated_khetma.number
        )
        await query.edit_message_text(
            text=utilities.create_khetma_message(updated_khetma),
            reply_markup=None,
            parse_mode="Markdown"
        )
        await context.bot.send_message(chat_id, completed_khetma_text, parse_mode="Markdown")


async def _handle_my_chapters(query, user, storage: KhetmaStorage):
    khetma_id = int(query.data.split("_")[2])
    try:
        chapters = storage.get_chapters_by_user(user.id, khetma_id=khetma_id)
    except errors.NoOwnedChapters:
        await query.answer("لا يوجد أي أجزاء محجوزة باسمك ⛔", show_alert=True)
        return

    chapters_text = " و ".join(str(ch.number) for ch in chapters)
    await query.answer(f"أجزاؤك في هذه الختمة: {chapters_text} 📋", show_alert=True)


async def _handle_info(query, khetma_id, chapter_number, storage: KhetmaStorage):
    chapter = storage.get_chapter(khetma_id=khetma_id, chapter_number=chapter_number)
    if not chapter:
        await query.answer(errors.KhetmaNotFoundError().message, show_alert=True)
        return

    if chapter.is_finished:
        await query.answer("✅ هذا الجزء تم الانتهاء منه بالفعل، جزاكم الله خيراً.", show_alert=True)
        return

    if chapter.is_reserved:
        await query.answer(
            f"الجزء {chapter_number} محجوز بواسطة {chapter.owner_username}",
            show_alert=True
        )
        return

    return chapter  # returns chapter only if it's available for reservation


async def _handle_reserve(query, user, chat_id, khetma_id, chapter_number, storage: KhetmaStorage, context):
    try:
        storage.reserve_chapter(
            khetma_id, chapter_number, user.id,
            await utilities.get_username(chat_id, user.id, context)
        )
    except (errors.ChapterAlreadyReservedError, errors.ChapterFinishedError) as e:
        await query.answer(e.message, show_alert=True)
        return

    updated_khetma = storage.get_khetma(khetma_id=khetma_id)
    new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
    await query.edit_message_text(
        text=utilities.create_khetma_message(updated_khetma),
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )
    await query.answer()

async def _handle_withdraw_all(query, user, chat_id, storage: KhetmaStorage, context):
    khetma_id = int(query.data.split("_")[2])
    try:
        withdrawn_chapters = storage.withdraw_all_user_chapters(chat_id, user.id, khetma_id)
    except errors.NoOwnedChapters:
        await query.answer("لا يوجد أي أجزاء محجوزة باسمك ⛔", show_alert=True)
        return

    chapters_text = " و ".join(str(ch.number) for ch in withdrawn_chapters)
    await query.answer(f"تم سحب الأجزاء: {chapters_text} 🔄", show_alert=True)

    updated_khetma = storage.get_khetma(khetma_id=khetma_id)
    new_keyboard = inline_keyboards.render_khetma_keyboard(updated_khetma)
    await query.edit_message_text(
        text=utilities.create_khetma_message(updated_khetma),
        reply_markup=new_keyboard,
        parse_mode="Markdown"
    )

async def handle_khetma_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat_id = update.effective_chat.id
    storage: KhetmaStorage = context.bot_data["khetma_storage"]

    if query.data.startswith("finish_all_"):
        await _handle_finish_all(query, user, chat_id, storage, context)
        return

    if query.data.startswith("my_chapters_"):
        await _handle_my_chapters(query, user, storage)
        return

    if query.data.startswith("withdraw_all_"):
        await _handle_withdraw_all(query, user, chat_id, storage, context)
        return

    # Reserve / Info
    callback_data = query.data.split("_")
    khetma_id = int(callback_data[1])
    chapter_number = int(callback_data[2])

    chapter = await _handle_info(query, khetma_id, chapter_number, storage)
    if chapter is None:
        return  # info was shown or error was answered

    await _handle_reserve(query, user, chat_id, khetma_id, chapter_number, storage, context)
   