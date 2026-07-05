import re
import webbrowser

from loguru import logger
from yt_dlp import YoutubeDL

_TITLE_OPTS = {"extract_flat": True, "quiet": True, "no_warnings": True, "simulate": True}


class BrowserState:
    """Состояние браузера: текущий открытый URL."""

    def __init__(self) -> None:
        self._current_url: str | None = None

    def open_url(self, url: str) -> None:
        """Открывает URL в браузере по умолчанию и запоминает его.

        Args:
            url: Ссылка для открытия.
        """
        try:
            self._current_url = url
            webbrowser.open(url)
        except Exception as ex:
            logger.bind(error=ex, url=url).error("Не удалось открыть браузер")

    def get_current_title(self) -> str | None:
        """Возвращает название текущего видео через yt-dlp.

        Returns:
            Очищенный заголовок или None, если видео не открыто / ошибка.
        """
        if not self._current_url:
            return None

        try:
            with YoutubeDL(_TITLE_OPTS) as ydl:
                info = ydl.extract_info(self._current_url, download=False)
        except Exception as ex:
            logger.bind(error=ex, url=self._current_url).warning(
                "Не удалось получить название видео"
            )
            return None

        if not info:
            return None
        title = info.get("title", "")
        return _clean_title(title) if title else None


_state = BrowserState()


def open_browser_url(url: str) -> None:
    """Открывает URL в браузере по умолчанию.

    Args:
        url: Ссылка для открытия.
    """
    _state.open_url(url)


def get_current_title() -> str | None:
    """Возвращает название текущего видео.

    Returns:
        Очищенный заголовок или None.
    """
    return _state.get_current_title()


def _clean_title(title: str) -> str:
    """Очищает заголовок от скобок, эмодзи и мусора."""
    title = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title)
    title = re.sub(r"[^\w\sА-Яа-яЁё.,!?]", " ", title)
    return re.sub(r"\s+", " ", title).strip()
