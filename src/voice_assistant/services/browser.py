import re

import webbrowser
from loguru import logger
from yt_dlp import YoutubeDL

_TITLE_OPTS = {"extract_flat": True, "quiet": True, "no_warnings": True, "simulate": True}

_current_url: str | None = None


def open_browser_url(url: str) -> None:
    """Открывает URL в браузере по умолчанию и запоминает его.

    Args:
        url: Ссылка для открытия.
    """
    global _current_url
    try:
        _current_url = url
        webbrowser.open(url)
    except Exception as ex:
        logger.bind(error=ex, url=url).error("Не удалось открыть браузер")


def get_current_title() -> str | None:
    """Возвращает название текущего видео через yt-dlp.

    Returns:
        Очищенный заголовок или None, если видео не открыто / ошибка.
    """
    if not _current_url:
        return None

    try:
        with YoutubeDL(_TITLE_OPTS) as ydl:
            info = ydl.extract_info(_current_url, download=False)
        if not info:
            return None
        title = info.get("title", "")
        return _clean_title(title) if title else None
    except Exception as ex:
        logger.bind(error=ex, url=_current_url).warning("Не удалось получить название видео")
        return None


def _clean_title(title: str) -> str:
    """Очищает заголовок от скобок, эмодзи и мусора."""
    title = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title)
    title = re.sub(r"[^\w\sА-Яа-яЁё.,!?]", " ", title)
    return re.sub(r"\s+", " ", title).strip()