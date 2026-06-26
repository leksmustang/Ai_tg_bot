import os
import tempfile
import base64
import aiohttp
import asyncio
import logging
from pdf2image import convert_from_path
from config import OPENROUTER_API_KEY, VISION_MODEL_GEMINI, VISION_MODEL_NEMOTRON, POPPLER_PATH, get_system_prompt

logger = logging.getLogger(__name__)

def get_vision_model_name(model_key: str) -> str:
    return VISION_MODEL_GEMINI if model_key == "gemini" else VISION_MODEL_NEMOTRON

async def pdf_to_images(file_path: str, dpi=200):
    loop = asyncio.get_event_loop()
    images = await loop.run_in_executor(
        None,
        lambda: convert_from_path(file_path, dpi=dpi, poppler_path=POPPLER_PATH)
    )
    images_base64 = []
    for img in images:
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img.save(tmp, 'JPEG')
            with open(tmp.name, "rb") as f:
                images_base64.append(base64.b64encode(f.read()).decode('utf-8'))
            os.remove(tmp.name)
    return images_base64

async def analyze_vision_file(file_path: str, file_type: str, user_prompt: str, user_data: dict, model_key: str, update=None) -> str:
    mode = user_data.get("mode", "friendly")
    system_prompt = get_system_prompt(mode)
    vision_model = get_vision_model_name(model_key)

    images_base64 = []
    if file_type == "document" and file_path.lower().endswith('.pdf'):
        if update:
            await update.message.reply_text("🔄 Конвертирую PDF в изображения...")
        images_base64 = await pdf_to_images(file_path)
        if not images_base64:
            return "⚠️ Не удалось конвертировать PDF."
    else:
        with open(file_path, "rb") as f:
            images_base64 = [base64.b64encode(f.read()).decode('utf-8')]

    content = [{"type": "text", "text": user_prompt}]
    for img in images_base64:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    payload = {
        "model": vision_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json=payload,
                timeout=60
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Vision API error {resp.status}: {error_text}")
                    return f"⚠️ Ошибка API (код {resp.status}). Попробуйте позже."

                result = await resp.json()
                if "choices" not in result or not result["choices"]:
                    logger.error(f"Unexpected response: {result}")
                    return "⚠️ Неожиданный ответ от API. Попробуйте позже."

                return result['choices'][0]['message']['content']

        except asyncio.TimeoutError:
            logger.error("Vision request timeout")
            return "⚠️ Превышено время ожидания ответа. Попробуйте позже."
        except Exception as e:
            logger.exception(f"Vision analysis error: {e}")
            return f"⚠️ Ошибка при анализе: {str(e)}"