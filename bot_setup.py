from decouple import config
from telegram.ext import ApplicationBuilder

# --- Load environment variables ---
BOT_TOKEN = config("BOT_TOKEN")
WEBHOOK_URL = config("WEBHOOK_URL")

# --- Initializing keys ---
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
