"""Открытие URL в Vivaldi в app-режиме (одно окно без вкладок).

На Windows используется Vivaldi с флагом --app=<url>, перед новым запуском
закрывается старое окно через taskkill — всегда одно окно, без копления вкладок.
На других ОС — fallback на webbrowser.open (Linux для dev/CI).
"""

from __future__ import annotations

import os
import platform
import subprocess
import webbrowser

from loguru import logger

from voice_assistant.config import settings
from voice_assistant.speech.text_normalize import clean_title

_IS_WINDOWS = platform.system() == "Windows"

if _IS_WINDOWS:
    from voice_assistant.services.windows_title import get_youtube_window_title
else:

    def get_youtube_window_title() -> str | None:
        return None


def _detect_vivaldi_path() -> str | None:
    """Авто-detect пути к vivaldi.exe на Windows.

    Проверяет типичные расположения: LOCALAPPDATA, Program Files, Program Files (x86).
    Возвращает путь к исполняемому файлу или None, если Vivaldi не найден.
    """
    if not _IS_WINDOWS:
        return None

    local_app_data = os.environ.get("LOCALAPPDATA")
    user_profile = os.environ.get("USERPROFILE")
    candidates: list[str] = []

    if local_app_data:
        candidates.append(os.path.join(local_app_data, "Vivaldi", "Application", "vivaldi.exe"))
    if user_profile:
        candidates.append(
            os.path.join(
                user_profile,
                "AppData",
                "Local",
                "Vivaldi",
                "Application",
                "vivaldi.exe",
            )
        )
    candidates.append(os.path.join("C:\\Program Files", "Vivaldi", "Application", "vivaldi.exe"))
    candidates.append(
        os.path.join("C:\\Program Files (x86)", "Vivaldi", "Application", "vivaldi.exe")
    )

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class BrowserState:
    """Состояние браузера: флаг открытого app-окна Vivaldi."""

    def __init__(self) -> None:
        self._has_open_window: bool = False

    def open_url(self, url: str) -> None:
        """Открывает URL в app-режиме Vivaldi (Windows) или webbrowser (fallback).

        На Windows перед новым запуском закрывает старое app-окно через taskkill,
        чтобы всегда было одно окно без копления вкладок.

        Args:
            url: Ссылка для открытия.
        """
        if not _IS_WINDOWS:
            try:
                webbrowser.open(url)
            except (webbrowser.Error, OSError) as ex:
                logger.bind(error=ex, url=url).error("Не удалось открыть браузер")
            return

        browser_path = settings.browser_path or _detect_vivaldi_path()
        if browser_path is None:
            logger.error("Vivaldi не найден — установите браузер или задайте BROWSER_PATH")
            return

        if self._has_open_window:
            subprocess.run(
                ["taskkill", "/IM", "vivaldi.exe"],  # noqa: S607
                capture_output=True,
                check=False,
            )
            self._has_open_window = False

        try:
            subprocess.Popen(  # noqa: S603
                [browser_path, f"--app={url}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._has_open_window = True
            logger.bind(url=url).info("Открыто app-окно Vivaldi")
        except OSError as ex:
            logger.bind(error=ex, url=url).error("Не удалось запустить Vivaldi")

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
        title = raw.split(" - YouTube")[0]
        return clean_title(title) if title else None


_state = BrowserState()


def open_browser_url(url: str) -> None:
    """Открывает URL в app-режиме Vivaldi (Windows) или webbrowser (fallback).

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
