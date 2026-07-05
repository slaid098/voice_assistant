import io
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import gtts
import pygame
from loguru import logger


def speak(text: str) -> None:
    """Озвучивает текст через gTTS и воспроизводит через pygame.

    Блокирующая — ждёт окончания воспроизведения.
    """
    _ensure_mixer()

    try:
        mp3_bytes = io.BytesIO()
        tts = gtts.gTTS(text, lang="ru", slow=False, lang_check=False)
        tts.write_to_fp(mp3_bytes)
        mp3_bytes.seek(0)

        with _temp_mp3_path(mp3_bytes) as path:
            _play_file(path)
    except Exception as ex:
        logger.bind(error=ex).warning("TTS generation or playback failed")


def _ensure_mixer() -> None:
    """Инициализирует pygame mixer один раз."""
    if pygame.mixer.get_init() is not None:
        return
    pygame.mixer.init(frequency=24000, size=-16, channels=1)


def _play_file(path: str) -> None:
    """Воспроизводит аудиофайл (блокирующе)."""
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
    except Exception as ex:
        logger.bind(error=ex).warning("Sound file playback failed")


@contextmanager
def _temp_mp3_path(mp3_bytes: io.BytesIO) -> Generator[str]:
    """Создаёт временный MP3-файл и удаляет его после использования."""
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(mp3_bytes.getvalue())
            temp_path = tmp.name
        yield temp_path
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)