from collections.abc import Callable
from enum import IntEnum
from importlib.resources import files
from pathlib import Path

import pygame
from loguru import logger

from voice_assistant.speech.tts import _ensure_mixer, speak

_SOUND_DIR: Path = files("voice_assistant") / "assets" / "sounds"
_sounds: dict[int, pygame.mixer.Sound] = {}


class Sound(IntEnum):
    """Звуковые ярлыки (earcons) для accessibility."""

    READY_TO_LISTEN = 1  # бип «говори» — перед каждой записью
    SEARCH_STARTED = 2   # чайм «поиск пошёл» — YouTube запрос принят
    STARTUP = 3          # фанфара «я проснулась» — один раз при старте
    DONE = 4             # финал «действие завершено / ошибка»


def init_sounds() -> None:
    """Загружает все 4 mp3 в память. Вызывается один раз при старте."""
    _ensure_mixer()
    for sound in Sound:
        path = _SOUND_DIR / f"{sound.value}.mp3"
        try:
            _sounds[sound.value] = pygame.mixer.Sound(str(path))
        except Exception as ex:
            logger.bind(error=ex, path=str(path)).warning("Не удалось загрузить звук")


def make_sound(sound: Sound) -> None:
    """Воспроизводит звук-ярлык (блокирующе — дослушивает до конца).

    Args:
        sound: Какой звук воспроизвести.
    """
    try:
        snd = _sounds.get(sound.value)
        if snd is None:
            logger.warning(f"Звук {sound.value} не загружен")
            return
        snd.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
    except Exception as ex:
        logger.bind(error=ex).warning(f"Не удалось воспроизвести звук {sound.value}")


def with_sound_effects(say_done: bool = False) -> Callable:
    """Декоратор: бип(READY_TO_LISTEN) до → функция → финал(DONE) после.

    Args:
        say_done: Произнести «Сделано» между функцией и финальным звуком.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> object:
            make_sound(Sound.READY_TO_LISTEN)
            result = func(*args, **kwargs)
            if say_done:
                speak("Сделано")
            make_sound(Sound.DONE)
            return result

        return wrapper

    return decorator