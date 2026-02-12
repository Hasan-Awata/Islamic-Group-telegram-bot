from decouple import config
import google.generativeai as genai
from telegram.ext import ApplicationBuilder

# --- Load environment variables ---
BOT_TOKEN = config("BOT_TOKEN")

# --- Initializing keys ---
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
