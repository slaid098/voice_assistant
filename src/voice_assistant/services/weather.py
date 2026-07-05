from typing import Any

import requests
from loguru import logger

from voice_assistant.config import settings

_GEOCODE_URL = "http://api.openweathermap.org/geo/1.0/direct"
_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

_OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь",
    51: "слабая морось",
    53: "морось",
    55: "сильная морось",
    56: "ледяная морось",
    57: "сильная ледяная морось",
    61: "небольшой дождь",
    63: "дождь",
    65: "сильный дождь",
    66: "ледяной дождь",
    67: "сильный ледяной дождь",
    71: "небольшой снег",
    73: "снег",
    75: "сильный снег",
    77: "снежные зёрна",
    80: "ливень",
    81: "сильный ливень",
    82: "очень сильный ливень",
    85: "снег с дождём",
    86: "сильный снег с дождём",
    95: "гроза",
    96: "гроза с градом",
    99: "сильная гроза с градом",
}


def get_weather_text(city: str | None = None) -> str:
    """Получить погоду по городу и вернуть текст для озвучки.

    Если задан OPENWEATHER_API_KEY — используется OpenWeather.
    Иначе — Open-Meteo (без ключа, бесплатно).

    Args:
        city: Город из голосовой команды.

    Returns:
        Готовый текст прогноза для TTS.
    """
    target = city or settings.weather_default_city

    if settings.openweather_api_key:
        return _get_openweather_text(target)
    return _get_open_meteo_text(target)


def _get_openweather_text(target: str) -> str:
    """Получить погоду через OpenWeather API (требует ключ)."""
    try:
        place = _resolve_city_openweather(target)
        if place is None:
            return "Не удалось определить город для прогноза."
        weather = _fetch_weather_openweather(place["lat"], place["lon"])
    except Exception as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error("Не удалось получить погоду")
        return "Не удалось получить прогноз погоды."
    else:
        return _format_weather(weather, place["name"])


def _get_open_meteo_text(target: str) -> str:
    """Получить погоду через Open-Meteo API (без ключа)."""
    try:
        place = _resolve_city_open_meteo(target)
        if place is None:
            return "Не удалось определить город для прогноза."
        weather = _fetch_weather_open_meteo(place["lat"], place["lon"])
    except Exception as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error("Не удалось получить погоду")
        return "Не удалось получить прогноз погоды."
    else:
        return _format_open_meteo_weather(weather, place["name"])


def _resolve_city_openweather(query: str) -> dict[str, Any] | None:
    """Найти координаты города через OpenWeather Geocoding API."""
    params: dict[str, str | int] = {"q": query, "limit": 1, "appid": settings.openweather_api_key}
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


def _fetch_weather_openweather(lat: float, lon: float) -> dict[str, Any]:
    """Получить текущую погоду по координатам через OpenWeather."""
    params: dict[str, str | float] = {
        "lat": lat,
        "lon": lon,
        "appid": settings.openweather_api_key,
        "units": "metric",
        "lang": "ru",
    }
    response = requests.get(_WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return dict(response.json())


def _format_weather(data: dict[str, Any], city: str) -> str:
    """Собрать естественный текст погоды для озвучки (OpenWeather)."""
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
        return (
            f"Сейчас в {city} {temp} градусов, {description}. "
            f"Ощущается как {feels_like}. "
            f"Ветер {wind} метров в секунду, влажность {humidity} процентов."
        )


def _resolve_city_open_meteo(query: str) -> dict[str, Any] | None:
    """Найти координаты города через Open-Meteo Geocoding API."""
    params: dict[str, str | int] = {"name": query, "count": 1, "language": "ru", "format": "json"}
    response = requests.get(_OPEN_METEO_GEOCODE_URL, params=params, timeout=10)
    response.raise_for_status()
    items = response.json().get("results")
    if not items:
        return None

    item = items[0]
    name = item.get("name") or query
    country = item.get("country")
    parts = [name]
    if country:
        parts.append(country)
    pretty_name = ", ".join(parts)
    return {"name": pretty_name, "lat": item["latitude"], "lon": item["longitude"]}


def _fetch_weather_open_meteo(lat: float, lon: float) -> dict[str, Any]:
    """Получить текущую погоду по координатам через Open-Meteo."""
    fields = "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
    params: dict[str, str | float] = {
        "latitude": lat,
        "longitude": lon,
        "current": fields,
        "timezone": "auto",
    }
    response = requests.get(_OPEN_METEO_WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return dict(response.json())


def _format_open_meteo_weather(data: dict[str, Any], city: str) -> str:
    """Собрать естественный текст погоды для озвучки (Open-Meteo)."""
    try:
        current = data["current"]
        temp = round(float(current["temperature_2m"]))
        feels_like = round(float(current["apparent_temperature"]))
        humidity = int(current["relative_humidity_2m"])
        wind = round(float(current["wind_speed_10m"]))
        wmo_code = int(current["weather_code"])
    except (KeyError, TypeError, ValueError) as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error(
            "Не удалось разобрать ответ погоды Open-Meteo",
        )
        return "Не удалось обработать данные о погоде."
    else:
        description = _wmo_description(wmo_code)
        return (
            f"Сейчас в {city} {temp} градусов, {description}. "
            f"Ощущается как {feels_like}. "
            f"Ветер {wind} метров в секунду, влажность {humidity} процентов."
        )


def _wmo_description(code: int) -> str:
    """Преобразовать WMO weather code в русское описание."""
    return _WMO_DESCRIPTIONS.get(code, "без уточнения")
