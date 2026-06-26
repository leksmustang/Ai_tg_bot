import logging
import datetime
import pytz
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import TELEGRAM_TOKEN
from database import init_db
from handlers.commands import (
    start, help_command, reset, status_command, buy_command, subscription_callback,
    unsubscribe, subscribe_remind, admin_command
)
from handlers.messages import handle_message
from utils.keyboards import get_main_keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Напоминания (как в первом боте)
async def morning_reminder(context):
    text = "☀️ Доброе утро! Как настроение? Я тут, если хочешь поболтать или спросить о чём-то. 😊"
    for uid in context.bot_data.get("subscribers", []):
        try:
            await context.bot.send_message(uid, text)
        except Exception as e:
            logger.error(f"Reminder error {uid}: {e}")

async def afternoon_reminder(context):
    text = "🌸 Середина дня! Не забывайте отдыхать. Если есть вопросы — задавайте, с радостью помогу. 💡"
    for uid in context.bot_data["subscribers"]:
        try:
            await context.bot.send_message(uid, text)
        except Exception as e:
            logger.error(f"Reminder error {uid}: {e}")

async def evening_reminder(context):
    text = "🌙 Вечер близко. Хотите подвести итоги дня или просто расслабиться? Я здесь, чтобы составить компанию. 🎶"
    for uid in context.bot_data["subscribers"]:
        try:
            await context.bot.send_message(uid, text)
        except Exception as e:
            logger.error(f"Reminder error {uid}: {e}")

def main():
    init_db()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Загружаем подписчиков
    from database import get_subscribers
    subscribers = get_subscribers()
    app.bot_data["subscribers"] = subscribers

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("subscribe", subscribe_remind))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(subscription_callback, pattern="^(sub_15|sub_30|back_to_menu)$"))

    # Обработчик сообщений
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

    # JobQueue для напоминаний
    job_queue = app.job_queue
    if job_queue:
        moscow_tz = pytz.timezone("Europe/Moscow")
        times = [
            datetime.time(hour=9, minute=0, tzinfo=moscow_tz),
            datetime.time(hour=13, minute=0, tzinfo=moscow_tz),
            datetime.time(hour=17, minute=0, tzinfo=moscow_tz)
        ]
        job_queue.run_daily(morning_reminder, time=times[0], days=tuple(range(7)))
        job_queue.run_daily(afternoon_reminder, time=times[1], days=tuple(range(7)))
        job_queue.run_daily(evening_reminder, time=times[2], days=tuple(range(7)))

    logger.info("🚀 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()