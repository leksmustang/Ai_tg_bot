import asyncio
import logging
import replicate
import aiohttp
from config import REPLICATE_API_TOKEN

logger = logging.getLogger(__name__)

# Инициализация клиента Replicate
if REPLICATE_API_TOKEN:
    replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)
else:
    replicate_client = None

async def generate_image(prompt: str, retries: int = 2) -> bytes | None:
    """
    Генерирует изображение через Replicate (модель FLUX.1-schnell).
    Возвращает байты изображения или None.
    """
    if not replicate_client:
        logger.warning("REPLICATE_API_TOKEN не задан, генерация изображений недоступна")
        return None

    # Модель: black-forest-labs/flux-schnell
    model = "black-forest-labs/flux-schnell"

    for attempt in range(retries + 1):
        try:
            # Запуск предсказания (синхронный вызов, но выполняется асинхронно)
            # Используем run_in_executor, чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None,
                lambda: replicate_client.run(
                    model,
                    input={"prompt": prompt, "num_outputs": 1}
                )
            )

            # output — список URL-адресов изображений
            if output and isinstance(output, list) and len(output) > 0:
                image_url = output[0]
                # Скачиваем изображение по URL
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            return await resp.read()
                        else:
                            logger.error(f"Failed to download image from {image_url}")
                            return None
            else:
                logger.error("No output from Replicate")
                return None

        except Exception as e:
            logger.error(f"Replicate error (attempt {attempt+1}): {e}")
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
                continue
            else:
                return None

    return None