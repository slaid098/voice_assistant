"""Тонкий фасад для распознавания речи (dispatch по STT_PROVIDER).

Сохраняет публичные имена transcribe_audio() и STTNetworkError для обратной
совместимости — assistant.py и тесты импортируют их отсюда.
"""

import numpy as np
from loguru import logger

from voice_assistant.config import settings
from voice_assistant.speech.providers.stt.base import STTProvider
from voice_assistant.speech.providers.stt.google_stt import STTNetworkError as STTNetworkError
from voice_assistant.speech.providers.stt.google_stt import google_stt
from voice_assistant.speech.providers.stt.vosk_stt import vosk_stt

__all__ = ["STTNetworkError", "transcribe_audio"]


def transcribe_audio(audio: np.ndarray) -> str | None:
    """Распознаёт речь через активный STT-провайдер с fallback.

    Логика по настройке STT_PROVIDER:
      - google → [google, vosk] (Google основной, Vosk fallback при нет сети)
      - vosk → [vosk, google] (Vosk основной, Google fallback)
      - auto → [vosk, google] (local быстрее, cloud резерв)

    Args:
        audio: Numpy-массив аудио (int16, 16 kHz, mono).

    Returns:
        Текст в нижнем регистре или None при тишине (не распознано).

    Raises:
        STTNetworkError: если все cloud-провайдеры упали по сети.
    """
    providers = _active_providers()

    for provider in providers:
        if not provider.is_available():
            continue
        try:
            return provider.transcribe(audio)
        except STTNetworkError:
            logger.bind(provider=provider.name).warning(
                "STT-провайдер недоступен (сеть), пробую следующий"
            )
            continue
        except Exception as ex:
            logger.bind(error=ex, provider=provider.name).warning(
                "STT-провайдер недоступен, пробую следующий"
            )
            continue

    logger.error("Все STT-провайдеры недоступны")
    return None


def _active_providers() -> list[STTProvider]:
    """Возвращает провайдеры согласно настройке STT_PROVIDER.

    google → [google, vosk] (cloud основной, local fallback)
    vosk → [vosk, google] (local основной, cloud fallback)
    auto → [vosk, google] (local быстрее, cloud как резерв)
    """
    if settings.stt_provider in ("vosk", "auto"):
        return [vosk_stt, google_stt]
    return [google_stt, vosk_stt]
