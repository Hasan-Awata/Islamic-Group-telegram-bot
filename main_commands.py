from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        text="أهلاً بكم في بوت دلني على الطاعة ..",
        parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
