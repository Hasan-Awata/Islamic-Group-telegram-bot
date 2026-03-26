from telegram import Update
from telegram.ext import ContextTypes

_start_command_message = (
    "أهلاً بكم في بوت دلني على الطاعة ..\n"
    "**لتشغيل البوت:**\n"
    "1. أضف البوت إلى مجموعتك الخاصة\n"
    "2. استعمل الأمر /activate@{bot_username}\n"
    "3. يمكنك الآن استخدام البوت ضمن المجموعة"
    "**لمعرفة الميزات والأوامر:**\n"
    "/help"
)

_help_command_message = """
📖 *دليل استخدام البوت*
━━━━━━━━━━━━━━━━━━

*أوامر الأعضاء:*

تم {رقم الجزء} — الرد على رسالة الختمة لتسجيل إنهاء جزء أو أكثر
مثال: تم 5 و 12 و الثالث

أجزائي — عرض الأجزاء المحجوزة باسمك في هذه المجموعة

في أجزاء — عرض الأجزاء المتاحة في كل ختمة نشطة

*أزرار الختمة:*

{رقم} — حجز الجزء المتاح
⬜ — عرض اسم من حجز هذا الجزء
✅ — عرض رسالة اكتمال الجزء
قرأت جميع أجزائي ✅ — تسجيل إنهاء جميع أجزائك في هذه الختمة
أجزائي 📋 — عرض أجزاءك المحجوزة في هذه الختمة
سحب أجزائي 🔄 — إلغاء حجز جميع أجزائك في هذه الختمة

━━━━━━━━━━━━━━━━━━
*أوامر المشرفين فقط:*

/new\_khetma — إنشاء ختمة جديدة

سحب {رقم الجزء} — الرد على رسالة الختمة لسحب أي جزء بغض النظر عن صاحبه
مثال: سحب 3 و 7

تذكير — إرسال قائمة بالأعضاء الذين لم ينهوا أجزاءهم بعد
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        text=_start_command_message.format(bot_username=context.bot.get_bot().username),
        parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id,
        text=_help_command_message,
        parse_mode="Markdown"
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass
