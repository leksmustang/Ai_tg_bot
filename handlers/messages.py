import os
import re
import aiohttp
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_CONTACT
from database import get_user, save_user
from utils.helpers import can_send_message, increment_used, is_admin
from utils.keyboards import get_main_keyboard
from services.ai_client import get_ai_response
from services.vision_analyzer import analyze_vision_file
from services.math_engine import try_solve_math
from services.weather import get_weather
from services.image_generator import generate_image
from services.document_parser import extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
from services.voice_transcriber import transcribe_voice
from services.link_parser import fetch_and_parse_url

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # --- Фото ---
    if update.message.photo:
        if not can_send_message(user_id, user):
            await update.message.reply_text("❌ Лимит исчерпан. Купите подписку.", reply_markup=get_main_keyboard())
            return
        await update.message.reply_text("📸 Анализирую фото...")
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"temp_{user_id}.jpg"
        await file.download_to_drive(file_path)
        prompt = update.message.caption or "Опиши, что на фото."
        model = user.get("vision_model", "gemini")
        answer = await analyze_vision_file(file_path, "photo", prompt, user, model, update)
        os.remove(file_path)
        await update.message.reply_text(answer[:4096])
        increment_used(user)
        save_user(user)
        return

    # --- Документы ---
    if update.message.document:
        doc = update.message.document
        ext = doc.file_name.split('.')[-1].lower() if '.' in doc.file_name else ''
        if ext not in ("pdf", "docx", "txt"):
            await update.message.reply_text("Поддерживаются только PDF, DOCX, TXT.")
            return
        if not can_send_message(user_id, user):
            await update.message.reply_text("❌ Лимит исчерпан.")
            return
        await update.message.reply_text(f"📄 Читаю {doc.file_name}...")
        file = await doc.get_file()
        data = await file.download_as_bytearray()
        if ext == "pdf":
            text = await asyncio.to_thread(extract_text_from_pdf, data)
        elif ext == "docx":
            text = await asyncio.to_thread(extract_text_from_docx, data)
        else:
            text = await asyncio.to_thread(extract_text_from_txt, data)
        if not text.strip():
            await update.message.reply_text("Файл пуст или не содержит текста.")
            return
        if len(text) > 12000:
            text = text[:12000] + "\n... (обрезано)"
        question = update.message.caption or "Сделай краткое содержание и выдели ключевые моменты."
        prompt = f"Документ:\n{text}\n\nЗадача: {question}"
        answer = await get_ai_response(user_id, prompt, user)
        await update.message.reply_text(answer[:4096])
        increment_used(user)
        save_user(user)
        return

    # --- Голосовые ---
    if update.message.voice:
        if not can_send_message(user_id, user):
            await update.message.reply_text("❌ Лимит исчерпан.")
            return
        await update.message.reply_text("🎤 Расшифровываю голосовое...")
        file = await update.message.voice.get_file()
        file_path = f"temp_{user_id}.ogg"
        await file.download_to_drive(file_path)
        transcribed = await transcribe_voice(file_path)
        os.remove(file_path)
        if not transcribed:
            await update.message.reply_text("Не удалось распознать речь.")
            return
        await update.message.reply_text(f"📝 {transcribed}")
        answer = await get_ai_response(user_id, transcribed, user)
        await update.message.reply_text(answer[:4096])
        increment_used(user)
        save_user(user)
        return

    # --- Текст ---
    text = update.message.text

    # Кнопки меню
    if text == "📘 Строгий ассистент":
        user["mode"] = "strict"
        save_user(user)
        await update.message.reply_text("✅ Включён строгий режим.", reply_markup=get_main_keyboard())
        return
    if text == "🤗 Дружелюбный ассистент":
        user["mode"] = "friendly"
        save_user(user)
        await update.message.reply_text("✅ Включён дружелюбный режим.", reply_markup=get_main_keyboard())
        return
    if text == "👤 Мой статус":
        from handlers.commands import status_command
        await status_command(update, context)
        return
    if text == "💎 Подписка / Купить":
        from handlers.commands import buy_command
        await buy_command(update, context)
        return
    if text == "🔍 Сменить модель анализа":
        current = user.get("vision_model", "gemini")
        new_model = "nemotron" if current == "gemini" else "gemini"
        user["vision_model"] = new_model
        save_user(user)
        await update.message.reply_text(f"🔄 Модель анализа: {'Gemini' if new_model=='gemini' else 'Nemotron'}", reply_markup=get_main_keyboard())
        return
    if text == "🆘 Помощь":
        await update.message.reply_text(f"🆘 По вопросам: {ADMIN_CONTACT}", reply_markup=get_main_keyboard())
        return

    # --- Генерация изображений ---
    if re.search(r"(нарисуй|сгенерируй|draw|generate)", text, re.I):
        if not can_send_message(user_id, user):
            await update.message.reply_text("❌ Лимит исчерпан. Купите подписку.", reply_markup=get_main_keyboard())
            return
        prompt = re.sub(r"(нарисуй|сгенерируй|draw|generate)", "", text, flags=re.I).strip(" :,-")
        if not prompt:
            await update.message.reply_text("Уточни, что нарисовать.")
            return
        await update.message.reply_text("🎨 Генерирую изображение...")
        img_bytes = await generate_image(prompt)
        if img_bytes:
            await update.message.reply_photo(photo=img_bytes, caption=f"«{prompt}»")
            increment_used(user)
            save_user(user)
        else:
            await update.message.reply_text("Не удалось сгенерировать изображение. Попробуйте позже.")
        return

    # --- Погода ---
    if re.search(r"(погода|weather|температура)", text, re.I):
        city = re.sub(r"(погода|weather|температура|в|во|на)", "", text, flags=re.I).strip(" :,?")
        if not city:
            await update.message.reply_text("Укажите город, например: погода Москва")
            return
        weather = await get_weather(city)
        if weather:
            await update.message.reply_text(weather)
        else:
            await update.message.reply_text(f"Не найден город «{city}».")
        return

    # --- Математика ---
    math_result = None
    if re.search(r"(реши|вычисли|посчитай|уравнение|производн|интеграл|simplify|solve|calculate)", text, re.I) or "=" in text:
        math_result = await asyncio.to_thread(try_solve_math, text)

    # --- Ссылки ---
    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        await update.message.reply_text("🔍 Читаю ссылки...")
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_and_parse_url(session, url) for url in urls[:3]]
            extracted = await asyncio.gather(*tasks)
        successful = [t for t in extracted if t]
        if successful:
            text += "\n\nСодержимое ссылок:\n" + "\n---\n".join(successful)
        else:
            await update.message.reply_text("Не удалось извлечь содержимое ссылок.")

    # Проверка лимита
    if not can_send_message(user_id, user):
        await update.message.reply_text("❌ Бесплатные запросы кончились. Приобретите подписку.", reply_markup=get_main_keyboard())
        return

    # Формируем запрос к LLM
    if math_result:
        user_query = f"{text}\n\n[Точный результат вычисления: {math_result}]\n\n(Используй этот результат как есть, не пересчитывай.)\nОформи ответ пользователю."
    else:
        user_query = text

    await update.message.chat.send_action(action="typing")
    answer = await get_ai_response(user_id, user_query, user)
    await update.message.reply_text(answer[:4096])
    increment_used(user)
    save_user(user)