import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# ── تنظیمات ──────────────────────────────────────────────
TELEGRAM_TOKEN = "8863821301:AAEs75IKSu-1aqqVJejWqu4_aI1-idI-kmA"
GEMINI_API_KEY = "AQ.Ab8RN6I0MLXWFyUmqJuDLmFikX5l8ykLTf9fiNiBVGeaM70jsw"

# ── تنظیم Gemini ──────────────────────────────────────────
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "تو یک دستیار هوشمند فارسی‌زبان هستی. "
        "پاسخ‌های واضح، مفید و دوستانه به فارسی بده. "
        "اگه سوال به زبان دیگه‌ای بود، به همون زبان جواب بده."
    )
)

# ── لاگ‌گیری ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── نگه‌داری تاریخچه مکالمه برای هر کاربر ──────────────
chat_sessions: dict[int, any] = {}

# ── هندلر /start ──────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {user_name}! 👋\n"
        "من یک دستیار هوش مصنوعی هستم.\n"
        "هر سوالی داری بپرس، خوشحال می‌شم کمک کنم! 🤖"
    )

# ── هندلر /clear ──────────────────────────────────────────
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions.pop(user_id, None)
    await update.message.reply_text("✅ تاریخچه مکالمه پاک شد!")

# ── هندلر /help ───────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *دستورات موجود:*\n\n"
        "/start - شروع مکالمه\n"
        "/clear - پاک کردن تاریخچه\n"
        "/help - راهنما\n\n"
        "کافیه پیامت رو بنویسی تا جواب بگیری! 💬",
        parse_mode="Markdown"
    )

# ── هندلر پیام‌های متنی ───────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])

        chat = chat_sessions[user_id]
        response = chat.send_message(user_text)
        reply = response.text

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"خطا: {e}")
        await update.message.reply_text(
            "⚠️ متأسفم، مشکلی پیش اومد. لطفاً دوباره امتحان کن."
        )

# ── راه‌اندازی بات ────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ بات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
