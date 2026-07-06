from typing import Any

from yt_dlp import YoutubeDL

from voice_assistant.config import settings
from voice_assistant.speech.text_normalize import clean_title

_YTDL_OPTS = {"extract_flat": True, "quiet": True, "no_warnings": True, "simulate": True}


def search_youtube_videos(query: str) -> list[dict[str, Any]]:
    """Ищет видео на YouTube через yt-dlp.

    Args:
        query: Поисковый запрос.

    Returns:
        Список словарей с ключами 'title' и 'url'.
    """
    try:
        with YoutubeDL(_YTDL_OPTS) as ydl:
            info = ydl.extract_info(
                f"ytsearch{settings.youtube_search_limit}:{query}", download=False
            )
        entries = info.get("entries", []) if info else []
        return [_format_entry(e) for e in entries if isinstance(e, dict)]
    except Exception:
        return []


def _format_entry(entry: dict[str, Any]) -> dict[str, str]:
    """Форматирует запись yt-dlp в простой словарь."""
    title = entry.get("title", "")

    url = (
        entry.get("url")
        or entry.get("webpage_url")
        or f"https://www.youtube.com/watch?v={entry.get('id')}"
    )
    return {
        "title": clean_title(title),
        "url": url,
    }
