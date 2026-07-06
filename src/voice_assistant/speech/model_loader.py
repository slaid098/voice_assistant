"""Разрешение путей к моделям и их предзагрузка.

Модели лежат в папке ``models/`` рядом с exe (PyInstaller) или в корне проекта
(разработка). Каждый провайдер имеет свою подпапку:

    models/
    ├── piper/          ← PIPER_MODEL (.onnx + .json)
    ├── vosk_stt/       ← VOSK_STT_MODEL (папка модели)
    └── vosk_tts/       ← VOSK_TTS_MODEL (папка модели)

Если модель отсутствует — vosk_tts библиотека скачивает автоматически
(fallback). Для остальных провайдеров модель должна быть в релизе.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from voice_assistant.config import settings


def models_dir() -> Path:
    """Возвращает путь к папке ``models/``.

    PyInstaller: рядом с exe. Разработка: в корне проекта (cwd).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "models"
    return Path.cwd() / "models"


def piper_model_path() -> Path:
    """Путь к .onnx файлу модели Piper."""
    return models_dir() / "piper" / settings.piper_model


def piper_config_path() -> Path:
    """Путь к .json конфигу модели Piper (рядом с .onnx)."""
    return piper_model_path().with_suffix(".onnx.json")


def vosk_stt_model_path() -> Path:
    """Путь к папке модели Vosk STT."""
    return models_dir() / "vosk_stt" / settings.vosk_stt_model


def vosk_tts_model_path() -> Path:
    """Путь к папке модели Vosk TTS."""
    return models_dir() / "vosk_tts" / settings.vosk_tts_model


def ensure_vosk_tts_model() -> bool:
    """Проверяет наличие модели Vosk TTS, скачивает при отсутствии.

    Библиотека vosk_tts умеет скачивать автоматически в ~/.cache/vosk/.
    Если локальная папка models/vosk_tts/ отсутствует — используем авто-скач.

    Returns:
        True если модель готова к работе.
    """
    local_path = vosk_tts_model_path()
    if local_path.exists() and any(local_path.iterdir()):
        logger.info(f"Модель Vosk TTS найдена локально: {local_path}")
        return True

    logger.info(
        "Локальная модель Vosk TTS не найдена, будет использовано авто-скачивание в ~/.cache/vosk/"
    )
    return False
