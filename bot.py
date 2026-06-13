import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

# ── تنظیمات ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

# ── لاگ‌گیری ──────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── کلاینت Anthropic ──────────────────────────────────────
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── نگه‌داری تاریخچه مکالمه برای هر کاربر ──────────────
conversation_history: dict[int, list] = {}

# ── هندلر /start ──────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {user_name}! 👋\n"
        "من یک دستیار هوش مصنوعی هستم.\n"
        "هر سوالی داری بپرس، خوشحال می‌شم کمک کنم! 🤖"
    )

# ── هندلر /clear (پاک کردن تاریخچه) ─────────────────────
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history.pop(user_id, None)
    await update.message.reply_text("✅ تاریخچه مکالمه پاک شد. می‌تونی از نو شروع کنی!")

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

    # نمایش "در حال تایپ..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # اضافه کردن پیام کاربر به تاریخچه
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    # محدود کردن تاریخچه به ۲۰ پیام آخر
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "تو یک دستیار هوشمند فارسی‌زبان هستی. "
                "پاسخ‌های واضح، مفید و دوستانه به فارسی بده. "
                "اگر سوال به زبان دیگه‌ای بود، به همون زبان جواب بده."
            ),
            messages=conversation_history[user_id]
        )

        assistant_reply = response.content[0].text

        # اضافه کردن پاسخ به تاریخچه
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

        await update.message.reply_text(assistant_reply)

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
