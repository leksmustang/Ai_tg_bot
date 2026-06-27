import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Текстовая модель для обычного общения (бесплатная)
# Актуальные бесплатные текстовые модели на OpenRouter:
# deepseek/deepseek-chat:free, meta-llama/llama-3-8b-instruct:free,
# microsoft/phi-3-mini-128k-instruct:free, mistralai/mistral-7b-instruct:free
TEXT_MODEL = os.getenv("TEXT_MODEL", "deepseek/deepseek-chat:free")

# Модель для vision
VISION_MODEL = os.getenv("VISION_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")

# Модели для генерации изображений (Hugging Face)
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

# Специфические vision-модели для анализа изображений/PDF 
VISION_MODEL_GEMINI = os.getenv("VISION_MODEL_GEMINI", "google/gemini-2.0-flash-lite-preview-02-05:free")
VISION_MODEL_NEMOTRON = os.getenv("VISION_MODEL_NEMOTRON", "nvidia/nemotron-nano-12b-v2-vl:free")

FREE_REQUESTS_PER_WEEK = int(os.getenv("FREE_REQUESTS_PER_WEEK", "30"))
ADMINS = [int(x.strip()) for x in os.getenv("ADMINS", "").split(",") if x.strip()]
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "@admin")
POPPLER_PATH = os.getenv("POPPLER_PATH", None)

# Системные промпты 
STRICT_PROMPT = (
    "Ты — строгий, точный и лаконичный ассистент. Твои ответы должны быть:\n"
    "- чёткими, по делу, без лишних слов и эмоций\n"
    "- фактическими, без предположений и домыслов\n"
    "- структурированными (используй списки, нумерацию, если уместно)\n"
    "- не используй эмодзи, не отвечай на личные вопросы\n"
    "Если не знаешь — честно скажи. Не додумывай. Отвечай на языке пользователя."
)

FRIENDLY_PROMPT = (
    "Ты — дружелюбный, весёлый и тёплый собеседник. Твои ответы:\n"
    "- живые, с лёгким юмором, поддерживающие\n"
    "- используй эмодзи (😊, 👍, 💡) умеренно\n"
    "- задавай уточняющие вопросы, проявляй интерес\n"
    "- помогай, советуй, подбадривай, но не переходи на личности\n"
    "Отвечай на языке пользователя."
)

def get_system_prompt(mode: str) -> str:
    return STRICT_PROMPT if mode == "strict" else FRIENDLY_PROMPT