from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    buttons = [
        [KeyboardButton("📘 Строгий ассистент")],
        [KeyboardButton("🤗 Дружелюбный ассистент")],
        [KeyboardButton("👤 Мой статус")],
        [KeyboardButton("💎 Подписка / Купить")],
        [KeyboardButton("🔍 Сменить модель анализа")],
        [KeyboardButton("🆘 Помощь")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)