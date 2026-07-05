"""Windows-specific: чтение заголовка окна браузера через win32gui.

На других ОС импорт этого модуля падает в ImportError,
поэтому browser.py импортирует его условно.
"""

from __future__ import annotations

import win32gui


def get_youtube_window_title() -> str | None:
    """Возвращает заголовок окна браузера с YouTube.

    Returns:
        Сырой заголовок окна (например, "Song - YouTube - Google Chrome")
        или None, если окно не найдено.
    """
    titles: list[str] = []

    def _enum_callback(hwnd: int, _: object) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if title and "YouTube" in title:
            titles.append(title)
        return True

    try:
        win32gui.EnumWindows(_enum_callback, None)
    except Exception:
        return None

    return titles[0] if titles else None
