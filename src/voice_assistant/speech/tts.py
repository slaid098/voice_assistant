import tempfile
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path

import pygame
from loguru import logger

from voice_assistant.speech.mixer import ensure_mixer as _ensure_mixer
from voice_assistant.speech.providers.base import TTSProvider
from voice_assistant.speech.providers.google_tts import google_tts
from voice_assistant.speech.providers.piper_tts import piper_tts

_providers: list[TTSProvider] = [google_tts, piper_tts]


def speak(text: str, *, on_all_fail: Callable[[], None] | None = None) -> None:
    """Озвучивает текст через любой доступный TTS-провайдер.

    Логика fallback:
    1. Google TTS (онлайн) — основной
    2. Piper TTS (офлайн ONNX) — fallback при сетевой ошибке
    3. on_all_fail callback — last resort (звук ошибки)

    Args:
        text: Текст для озвучки.
        on_all_fail: Callback если все провайдеры упали (например, make_sound).
    """
    _ensure_mixer()

    for provider in _providers:
        if not provider.is_available():
            continue
        try:
            audio_bytes = provider.synthesize(text)
        except Exception as ex:
            logger.bind(error=ex, provider=type(provider).__name__).warning(
                "TTS-провайдер недоступен, пробую следующий"
            )
            continue
        else:
            _play_bytes(audio_bytes)
            return

    logger.error("Все TTS-провайдеры недоступны")
    if on_all_fail is not None:
        on_all_fail()


def _play_bytes(audio_bytes: bytes) -> None:
    """Воспроизводит аудио-байты через pygame (блокирующе)."""
    suffix = ".mp3" if _is_mp3(audio_bytes) else ".wav"
    with _temp_audio_path(audio_bytes, suffix) as path:
        _play_file(path)


def _is_mp3(data: bytes) -> bool:
    """Проверяет, MP3 ли это (по заголовку ID3 или MPEG frame)."""
    return data[:3] == b"ID3" or (data[:2] == b"\xff\xfb" or data[:2] == b"\xff\xf3")


def _play_file(path: str) -> None:
    """Воспроизводит аудиофайл (блокирующе)."""
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
    except Exception as ex:
        logger.bind(error=ex).warning("Не удалось воспроизвести аудиофайл")


@contextmanager
def _temp_audio_path(audio_bytes: bytes, suffix: str) -> Generator[str]:
    """Создаёт временный аудиофайл и удаляет его после использования."""
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        yield temp_path
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
