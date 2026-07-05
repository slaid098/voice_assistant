import re
import sys
import webbrowser

from loguru import logger

_IS_WINDOWS = sys.platform == "win32"

if _IS_WINDOWS:
    from voice_assistant.services.windows_title import get_youtube_window_title
else:

    def get_youtube_window_title() -> str | None:
        return None


class BrowserState:
    """Состояние браузера: последний открытый URL."""

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
        """Возвращает название ТЕКУЩЕГО видео из заголовка окна браузера.

        Использует win32gui (Windows) — ловит autoplay и смену видео.
        На других ОС или если окно не найдено — возвращает None.

        Returns:
            Очищенный заголовок или None.
        """
        raw = get_youtube_window_title()
        if not raw:
            return None
        # "Video Title - YouTube - Google Chrome" → "Video Title"
        title = raw.split(" - YouTube")[0]
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
