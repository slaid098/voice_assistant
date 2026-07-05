#!/usr/bin/env python3
"""Предгенерация фиксированных фраз через Google TTS (gTTS).

Скрипт для разработчика. Запускается вручную при добавлении/изменении фраз:
    uv run python scripts/gen_phrases.py

Синтезирует все фиксированные фразы из PHRASES через gTTS (lang=ru) и
сохраняет MP3-файлы в assets/sounds/phrases/ + manifest.json (маппинг
текст→имя_файла). Файлы коммитятся в репозиторий — на runtime фразы
играются из ассетов мгновенно, без обращения к Google.

Динамические фразы (с подставляемыми значениями: время, погода, названия
видео) НЕ предгенерируются — их текст каждый раз новый.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import gtts

PHRASES_DIR = Path("src/voice_assistant/assets/sounds/phrases")
MANIFEST_PATH = PHRASES_DIR / "manifest.json"

# Транслитерация RU→LAT для имён файлов (без внешних зависимостей).
_TRANSLIT = str.maketrans(
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
    "abvgdeejzijklmnoprstufhccss_y_euaABVGDEEJZIJKLMNOPRSTUFHCCSS_Y_EUA",
)


def _slugify(text: str) -> str:
    """Превращает русский текст в безопасное имя файла (латиница)."""
    slug = text.translate(_TRANSLIT)
    slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_").lower()[:60]


# Все фиксированные фразы ассистента (точный текст из speak() вызовов).
# Динамические (f-строки с {переменными}) сюда НЕ входят.
PHRASES: list[str] = [
    # assistant.py
    "Слушаю.",
    "Не получается. Скажите слово активации снова.",
    "Я вас не поняла, повторите.",
    "Нет связи с интернетом.",
    # handlers.py
    "Нечего отменять.",
    "Сейчас ничего не играет.",
    "Я не знаю такую команду.",
    # commands.py
    "Укажите время для таймера. Например: таймер пять минут.",
    "Не расслышала время. Повторите, например: таймер пять минут.",
    # youtube_flow.py
    "Что найти?",
    "Ищу.",
    "Ничего не найдено.",
    "Поиск отменён.",
    "Не поняла. Скажите: включить, дальше или назад.",
    "Включаю.",
    "Сделано.",
    "Это последнее видео. Скажите: включить, назад или стоп.",
    "Это первое видео. Скажите: включить, дальше или стоп.",
    # commands.py — help (одна длинная фраза)
    (
        "Вот что я умею. "
        "Скажите ютуб и запрос — я найду видео. "
        "Во время поиска скажите стоп — отменю поиск. "
        "Скажите погода — расскажу погоду. "
        "Скажите время — скажу текущее время. "
        "Скажите таймер — поставлю таймер. "
        "Скажите название — скажу, что сейчас играет."
    ),
    # Фраза-признак перед долгими действиями (погода, YouTube-поиск)
    "Выполняю.",
    # cli.py — crash handler
    "Произошла критическая ошибка. Программа завершит работу.",
    "Произошла ошибка. Повторите команду.",
]


def main() -> int:
    PHRASES_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {}
    used_filenames: set[str] = set()

    for phrase in PHRASES:
        slug = _slugify(phrase)
        filename = f"{slug}.mp3"
        # защита от коллизий
        if filename in used_filenames:
            filename = f"{slug}_{abs(hash(phrase)) % 1000:03d}.mp3"
        used_filenames.add(filename)

        out_path = PHRASES_DIR / filename
        print(f"Синтезирую: {phrase!r} → {filename}")
        try:
            tts = gtts.gTTS(phrase, lang="ru", slow=False, lang_check=False)
            tts.save(str(out_path))
        except Exception as ex:
            print(f"  ОШИБКА: {ex}", file=sys.stderr)
            return 1
        manifest[phrase] = filename

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"\nГотово: {len(manifest)} фраз → {PHRASES_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())