import asyncio
import logging
from openai import OpenAI
from config import OPENROUTER_API_KEY, TEXT_MODEL, get_system_prompt

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

async def get_ai_response(user_id: int, text: str, user_data: dict) -> str:
    """Асинхронный вызов OpenRouter для текста."""
    mode = user_data.get("mode", "friendly")
    history = user_data.get("history", [])
    if not history or history[0].get("role") != "system":
        history.insert(0, {"role": "system", "content": get_system_prompt(mode)})
    else:
        history[0]["content"] = get_system_prompt(mode)

    history.append({"role": "user", "content": text})
    if len(history) > 21:
        history[:] = [history[0]] + history[-20:]

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=TEXT_MODEL,
                messages=history,
                temperature=0.7,
                max_tokens=2000,
            )
        )
        answer = response.choices[0].message.content
        if answer:
            history.append({"role": "assistant", "content": answer})
        return answer or "Извините, не удалось сформулировать ответ."
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        return "⚠️ Ошибка при обращении к нейросети. Попробуйте позже."