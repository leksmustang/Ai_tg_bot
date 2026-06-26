import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_CONTACT, FREE_REQUESTS_PER_WEEK
from database import get_user, save_user, get_subscribers, get_all_users, add_subscriber, remove_subscriber
from utils.helpers import is_admin, has_active_subscription, get_remaining_requests
from utils.keyboards import get_main_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        user = {
            "user_id": user_id,
            "mode": "friendly",
            "free_used_week": 0,
            "week_start": None,
            "subscription_end": None,
            "paid": False,
            "vision_model": "gemini",
            "history": []
        }
        save_user(user)
    add_subscriber(user_id)
    welcome = (
        "✨ *Добро пожаловать!*\n\n"
        "Я — универсальный помощник.\n"
        "Умею:\n"
        "- отвечать на вопросы (строго или дружелюбно)\n"
        "- анализировать фото, PDF, документы (DOCX, TXT)\n"
        "- расшифровывать голосовые\n"
        "- решать математику (уравнения, производные, интегралы)\n"
        "- показывать погоду\n"
        "- генерировать изображения по запросу «нарисуй ...»\n"
        "- читать ссылки\n\n"
        f"🎁 Бесплатно: {FREE_REQUESTS_PER_WEEK} запросов в неделю\n"
        "💎 Подписка даёт безлимит.\n\n"
        "Выберите режим кнопками ниже."
    )
    await update.message.reply_text(welcome, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *Помощь*\n\n"
        "/start — начать\n"
        "/reset — очистить историю\n"
        "/status — мой статус\n"
        "/buy — подписка\n"
        "/calc <выражение> — математика\n"
        "/weather <город> — погода\n"
        "/image <описание> — генерация картинки\n"
        "/subscribe — подписаться на напоминания\n"
        "/unsubscribe — отписаться\n"
        "/admin — статистика (только админы)\n\n"
        f"По вопросам: {ADMIN_CONTACT}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user:
        user["history"] = []
        save_user(user)
    await update.message.reply_text("🧹 История диалога очищена.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user:
        user = {
            "user_id": user_id,
            "mode": "friendly",
            "free_used_week": 0,
            "week_start": None,
            "subscription_end": None,
            "paid": False,
            "vision_model": "gemini",
            "history": []
        }
        save_user(user)
    remaining = get_remaining_requests(user_id)
    sub_end = user.get("subscription_end")
    if sub_end and not is_admin(user_id):
        try:
            end_date = datetime.datetime.fromisoformat(sub_end)
            sub_status = f"✅ до {end_date.strftime('%d.%m.%Y %H:%M')} (МСК)"
        except:
            sub_status = "⚠️ ошибка"
    elif is_admin(user_id):
        sub_status = "👑 админ"
    else:
        sub_status = "❌ нет"

    mode = user.get("mode", "friendly")
    mode_name = "Строгий" if mode == "strict" else "Дружелюбный"
    vision = user.get("vision_model", "gemini")
    vision_name = "Gemini" if vision == "gemini" else "Nemotron"

    await update.message.reply_text(
        f"📊 *Статус*\n\n"
        f"Режим: {mode_name}\n"
        f"Модель анализа: {vision_name}\n"
        f"Запросов осталось: {remaining}\n"
        f"Подписка: {sub_status}",
        parse_mode="Markdown"
    )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📆 15 дней — 400₽", callback_data="sub_15")],
        [InlineKeyboardButton("📆 30 дней — 750₽", callback_data="sub_30")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ])
    await update.message.reply_text("💎 *Выберите тариф*", parse_mode="Markdown", reply_markup=keyboard)

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    remove_subscriber(update.effective_user.id)
    await update.message.reply_text("❌ Отписались от напоминаний.")

async def subscribe_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_subscriber(update.effective_user.id)
    await update.message.reply_text("✅ Подписались на напоминания.")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет прав.")
        return
    all_users = get_all_users()
    subs = get_subscribers()
    active = 0
    for uid in all_users:
        u = get_user(uid)
        if u and has_active_subscription(u):
            active += 1
    await update.message.reply_text(
        f"📊 *Статистика*\nВсего пользователей: {len(all_users)}\nАктивных подписок: {active}\nПодписчиков на рассылку: {len(subs)}",
        parse_mode="Markdown"
    )

async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    if data == "sub_15":
        days = 15
    elif data == "sub_30":
        days = 30
    else:
        await query.edit_message_text("🔙 Назад")
        return
    end_date = datetime.datetime.now(pytz.timezone("Europe/Moscow")) + datetime.timedelta(days=days)
    user = get_user(user_id)
    if not user:
        user = {
            "user_id": user_id,
            "mode": "friendly",
            "free_used_week": 0,
            "week_start": None,
            "subscription_end": None,
            "paid": False,
            "vision_model": "gemini",
            "history": []
        }
    user["subscription_end"] = end_date.isoformat()
    user["paid"] = True
    save_user(user)
    await query.edit_message_text(
        f"✅ Подписка на {days} дней активирована до {end_date.strftime('%d.%m.%Y %H:%M')} (МСК).",
        parse_mode="Markdown"
    )