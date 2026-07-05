import requests
from loguru import logger

from voice_assistant.config import OPENWEATHER_API_KEY, WEATHER_DEFAULT_CITY

_GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"
_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather_text(city: str | None = None) -> str:
    """Получить погоду по городу и вернуть текст для озвучки.

    Args:
        city: Город из голосовой команды.

    Returns:
        Готовый текст прогноза для TTS.
    """
    if not OPENWEATHER_API_KEY:
        return "Не настроен ключ погоды. Добавьте OPENWEATHER_API_KEY в файл .env."

    target = city or WEATHER_DEFAULT_CITY
    try:
        place = _resolve_city(target)
        if place is None:
            return "Не удалось определить город для прогноза."
        weather = _fetch_weather(place["lat"], place["lon"])
    except Exception as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error("Не удалось получить погоду")
        return "Не удалось получить прогноз погоды."
    else:
        return _format_weather(weather, place["name"])


def _resolve_city(query: str) -> dict | None:
    """Найти координаты города через OpenWeather Geocoding API."""
    params = {"q": query, "limit": 1, "appid": OPENWEATHER_API_KEY}
    response = requests.get(_GEOCODE_URL, params=params, timeout=10)
    response.raise_for_status()
    items = response.json()
    if not items:
        return None

    item = items[0]
    name = item.get("local_names", {}).get("ru") or item.get("name") or query
    state = item.get("state")
    country = item.get("country")
    parts = [name]
    if state:
        parts.append(state)
    if country:
        parts.append(country)
    pretty_name = ", ".join(parts)
    return {"name": pretty_name, "lat": item["lat"], "lon": item["lon"]}


def _fetch_weather(lat: float, lon: float) -> dict:
    """Получить текущую погоду по координатам."""
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    response = requests.get(_WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _format_weather(data: dict, city: str) -> str:
    """Собрать естественный текст погоды для озвучки."""
    try:
        temp = round(float(data["main"]["temp"]))
        feels_like = round(float(data["main"]["feels_like"]))
        humidity = int(data["main"]["humidity"])
        wind = round(float(data["wind"]["speed"]))
        weather = data["weather"][0]
        description = weather.get("description", "без уточнения")
    except (KeyError, IndexError, TypeError, ValueError) as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error(
            "Не удалось разобрать ответ погоды",
        )
        return "Не удалось обработать данные о погоде."
    else:
        result = (
            f"Сейчас в {city} {temp} градусов, {description}. "
            f"Ощущается как {feels_like}. "
            f"Ветер {wind} метров в секунду, влажность {humidity} процентов."
        )
        return result