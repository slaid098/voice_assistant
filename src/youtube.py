import re

from yt_dlp import YoutubeDL

from src.config import YOUTUBE_SEARCH_LIMIT

_YTDL_OPTS = {"extract_flat": True, "quiet": True, "no_warnings": True, "simulate": True}


def search_youtube_videos(query: str) -> list[dict]:
    """The SINGLE public function of this module.

    Searches YouTube via yt-dlp and returns a list of formatted video entries.
    Each entry is a dict with keys: 'title', 'url' (or webpage_url).
    """
    try:
        with YoutubeDL(_YTDL_OPTS) as ydl:
            info = ydl.extract_info(f"ytsearch{YOUTUBE_SEARCH_LIMIT}:{query}", download=False)
        entries = info.get("entries", []) if info else []
        return [_format_entry(e) for e in entries if isinstance(e, dict)]
    except Exception:
        return []


def _format_entry(entry: dict) -> dict:
    """Format single yt-dlp entry into simple title, url pair."""
    title = entry.get("title", "")
    clean_title_str = _clean_title(title)

    url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}"
    return {
        "title": clean_title_str,
        "url": url,
    }


def _clean_title(title: str) -> str:
    """Strip brackets, emojis, and bad characters."""
    title = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title)
    title = re.sub(r"[^\w\sА-Яа-яЁё.,!?]", " ", title)
    return re.sub(r"\s+", " ", title).strip()
