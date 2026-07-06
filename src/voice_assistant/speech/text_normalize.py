"""Нормализация текста перед TTS.

Текст от внешних источников (YouTube-заголовки, погода, браузер) может содержать
латиницу, цифры и символы, которые русские TTS-движки (Google lang=ru, Piper
ru_RU-irina) произносят плохо: «точка», «двоеточие», пропуск английских букв.

normalize_for_tts() применяется в speak() перед dispatch к провайдерам:
  1. Замена известных брендов на русскую транскрипцию (словарь топ-20).
  2. Транслитерация оставшейся латиницы через cyrtranslit (фонетика).

clean_title() используется сервисами (YouTube, browser) для очистки заголовков
от скобок/эмодзи перед нормализацией.
"""

from __future__ import annotations

import re

import cyrtranslit

_BRANDS: dict[str, str] = {
    "youtube music": "ютуб мьюзик",
    "youtube": "ютуб",
    "google": "гугл",
    "iphone": "айфон",
    "ipad": "айпад",
    "macbook": "макбук",
    "imac": "аймак",
    "whatsapp": "ватсап",
    "facebook": "фейсбук",
    "instagram": "инстаграм",
    "telegram": "телеграм",
    "tiktok": "тикток",
    "netflix": "нетфликс",
    "spotify": "спотифай",
    "github": "гитхаб",
    "openai": "опен ай",
    "chatgpt": "чат гпт",
    "microsoft": "майкрософт",
    "windows": "виндоус",
    "android": "андроид",
    "samsung": "самсунг",
    "apple": "эпл",
    "twitter": "твиттер",
}

_BRAND_PATTERN = re.compile(
    "|".join(re.escape(k) for k in sorted(_BRANDS, key=len, reverse=True)),
    flags=re.IGNORECASE,
)


def normalize_for_tts(text: str) -> str:
    """Нормализует текст для русского TTS: бренды → транслитерация.

    Args:
        text: Исходный текст (может содержать латиницу).

    Returns:
        Текст с латиницей, заменённой на кириллицу.
    """
    if not text:
        return text

    text = _BRAND_PATTERN.sub(lambda m: _BRANDS[m.group().lower()], text)

    if not _has_latin(text):
        return text

    return str(cyrtranslit.to_cyrillic(text, "ru"))


def _has_latin(text: str) -> bool:
    """Проверяет, есть ли в тексте латинские буквы."""
    return any("a" <= c.lower() <= "z" for c in text)


def clean_title(title: str) -> str:
    """Очищает заголовок от скобок, эмодзи и мусора.

    Регекс оставляет буквы (включая латиницу для последующей транслитерации),
    цифры, пробелы и базовую пунктуацию. Латиница убирается позже в
    normalize_for_tts() — здесь только структурная чистка.
    """
    title = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title)
    title = re.sub(r"[^\w\sА-Яа-яЁё.,!?]", " ", title)
    return re.sub(r"\s+", " ", title).strip()
