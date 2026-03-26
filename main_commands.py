from telegram import Update
from telegram.ext import ContextTypes

_start_command_message = (
    "أهلاً بكم في بوت دلني على الطاعة ..\n"
    "**لتشغيل البوت:**\n"
    "1. أضف البوت إلى مجموعتك الخاصة\n"
    "2. استعمل الأمر /start@{bot_username}\n"
    "**لمعرفة الميزات والأوامر:**\n"
    "/help"
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        text=_start_command_message.format(bot_username=context.bot.get_bot().username),
        parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
