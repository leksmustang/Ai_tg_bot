import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
from config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

_cache = {}
CACHE_TTL = 900  # 15 минут

WMO_CODES = {
    0: ("Ясно", "☀️"),
    1: ("Преимущественно ясно", "🌤️"),
    2: ("Переменная облачность", "⛅"),
    3: ("Облачно", "☁️"),
    45: ("Туман", "🌫️"),
    48: ("Туман с инеем", "🌫️"),
    51: ("Лёгкая морось", "🌦️"),
    53: ("Морось", "🌦️"),
    55: ("Сильная морось", "🌧️"),
    56: ("Ледяная морось", "🌧️"),
    57: ("Сильная ледяная морось", "🌧️"),
    61: ("Небольшой дождь", "🌧️"),
    63: ("Дождь", "🌧️"),
    65: ("Сильный дождь", "🌧️"),
    66: ("Ледяной дождь", "🌧️"),
    67: ("Сильный ледяной дождь", "🌧️"),
    71: ("Небольшой снег", "🌨️"),
    73: ("Снег", "🌨️"),
    75: ("Сильный снег", "❄️"),
    77: ("Снежные зёрна", "❄️"),
    80: ("Небольшие ливни", "🌦️"),
    81: ("Ливни", "🌧️"),
    82: ("Сильные ливни", "⛈️"),
    85: ("Небольшой снегопад", "🌨️"),
    86: ("Сильный снегопад", "❄️"),
    95: ("Гроза", "⛈️"),
    96: ("Гроза с небольшим градом", "⛈️"),
    99: ("Гроза с сильным градом", "⛈️"),
}

async def normalize_city_name(city: str) -> str:
    """Приводит название города к именительному падежу через LLM."""
    if not OPENROUTER_API_KEY:
        return city
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "openrouter/free",
                "messages": [
                    {"role": "system", "content": "Ты помощник, который приводит название города к именительному падежу и исправляет опечатки. Отвечай только названием города, без пояснений."},
                    {"role": "user", "content": city}
                ]
            }
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    logger.error(f"Normalize city error: {resp.status} {await resp.text()}")
                    return city
    except Exception as e:
        logger.error(f"Normalize city exception: {e}")
        return city

async def geocode_city(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "ru", "format": "json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=15) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            results = data.get("results")
            if not results:
                return None
            place = results[0]
            return {"name": place["name"], "lat": place["latitude"], "lon": place["longitude"]}

async def fetch_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=15) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

async def get_weather(city: str):
    cache_key = city.lower()
    if cache_key in _cache and datetime.now() - _cache[cache_key]["time"] < timedelta(seconds=CACHE_TTL):
        return _cache[cache_key]["data"]

    # Пробуем геокодировать исходный город
    place = await geocode_city(city)
    if not place:
        # Если не найден, пробуем нормализовать через LLM
        normalized = await normalize_city_name(city)
        if normalized and normalized.lower() != city.lower():
            place = await geocode_city(normalized)
            if place:
                city = normalized  # обновляем для отображения

    if not place:
        return None

    data = await fetch_weather(place["lat"], place["lon"])
    if not data:
        return None

    current = data.get("current", {})
    code = current.get("weather_code")
    description, emoji = WMO_CODES.get(code, ("Неизвестно", "🌡️"))
    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")

    result = (
        f"{emoji} Погода в {place['name']}\n\n"
        f"{description}\n"
        f"Температура: {temp}°C (ощущается как {feels}°C)\n"
        f"Влажность: {humidity}%\n"
        f"Ветер: {wind} км/ч"
    )
    _cache[cache_key] = {"data": result, "time": datetime.now()}
    return result