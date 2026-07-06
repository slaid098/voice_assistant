import io
import threading
from collections import OrderedDict
from collections.abc import Callable

import pygame
from loguru import logger

from voice_assistant.config import settings
from voice_assistant.speech.mixer import ensure_mixer as _ensure_mixer
from voice_assistant.speech.providers.base import TTSProvider
from voice_assistant.speech.providers.google_tts import google_tts
from voice_assistant.speech.providers.piper_tts import piper_tts
from voice_assistant.speech.providers.vosk_tts import vosk_tts
from voice_assistant.speech.text_normalize import normalize_for_tts

_dynamic_cache: OrderedDict[str, pygame.mixer.Sound] = OrderedDict()


def speak(text: str, *, on_all_fail: Callable[[], None] | None = None) -> None:
    """Озвучивает текст через активный TTS-провайдер.

    Текст нормализуется (латиница → кириллица) перед синтезом, чтобы русские
    TTS-движки корректно произносили английские слова в русских фразах.

    Логика по типу провайдера:
      - cloud (Google): фиксированные фразы из ассетов → LRU-кэш динамики →
        синтез через сеть с кэшированием результата. Fallback на local.
      - local (Piper): синтез на лету, без кэша (мгновенно локально).
      - auto: local → cloud (локальный быстрее, cloud как резерв).

    Args:
        text: Текст для озвучки.
        on_all_fail: Callback если все провайдеры упали (например, make_sound).
    """
    _ensure_mixer()
    text = normalize_for_tts(text)
    providers = _active_providers()

    if not providers:
        logger.error("Нет активных TTS-провайдеров")
        _call_on_fail(on_all_fail)
        return

    primary = providers[0]
    if primary.is_cloud and _try_cloud_cache(primary, text):
        return

    if _synthesize_first_available(providers, text):
        return

    logger.error("Все TTS-провайдеры недоступны")
    _call_on_fail(on_all_fail)


def _call_on_fail(on_all_fail: Callable[[], None] | None) -> None:
    """Вызывает callback при отказе всех провайдеров."""
    if on_all_fail is not None:
        on_all_fail()


def _synthesize_first_available(providers: list[TTSProvider], text: str) -> bool:
    """Перебирает провайдеры, синтезирует и проигрывает первый доступный.

    Для cloud-провайдеров результат кэшируется в LRU.
    Returns:
        True, если фраза синтезирована и воспроизведена. False — все недоступны.
    """
    for provider in providers:
        if not provider.is_available():
            continue
        try:
            audio_bytes = provider.synthesize(text)
        except Exception as ex:
            logger.bind(error=ex, provider=type(provider).__name__).warning(
                "TTS-провайдер недоступен, пробую следующий"
            )
            continue

        if provider.is_cloud:
            sound = _bytes_to_sound(audio_bytes)
            if sound is not None:
                _cache_dynamic(text, sound)
                _play_sound(sound)
                return True
        _play_bytes(audio_bytes)
        return True
    return False


def _active_providers() -> list[TTSProvider]:
    """Возвращает провайдеры согласно настройке TTS_PROVIDER.

    google → [google, piper] (cloud основной, local fallback)
    piper → [piper, google] (local основной, cloud fallback)
    vosk  → [vosk, google, piper] (local основной, cloud+local fallback)
    auto  → [piper, google] (local быстрее, cloud как резерв)
    """
    if settings.tts_provider in {"piper", "auto"}:
        return [piper_tts, google_tts]
    if settings.tts_provider == "vosk":
        return [vosk_tts, google_tts, piper_tts]
    return [google_tts, piper_tts]


def _try_cloud_cache(provider: TTSProvider, text: str) -> bool:
    """Ищет фразу в ассетах и LRU-кэше (только для cloud-провайдера).

    Returns:
        True, если фраза найдена и воспроизведена. False — нужно синтезировать.
    """
    fixed = provider.fixed_phrase(text)
    if fixed is not None:
        sound = _bytes_to_sound(fixed)
        if sound is not None:
            logger.bind(source="fixed_phrases").debug(f"Фраза из ассетов: {text!r}")
            _play_sound(sound)
            return True

    cached = _lookup_dynamic_cache(text)
    if cached is not None:
        _play_sound(cached)
        return True

    return False


def _lookup_dynamic_cache(text: str) -> pygame.mixer.Sound | None:
    """Ищет фразу в LRU-кэше динамических фраз. При попадании — поднимает наверх."""
    if text not in _dynamic_cache:
        return None
    _dynamic_cache.move_to_end(text)
    logger.bind(source="dynamic_cache").debug(f"Фраза из кэша: {text!r}")
    return _dynamic_cache[text]


def _cache_dynamic(text: str, sound: pygame.mixer.Sound) -> None:
    """Кэширует синтезированную фразу в LRU-кэше с лимитом."""
    _dynamic_cache[text] = sound
    while len(_dynamic_cache) > settings.tts_cache_size:
        _dynamic_cache.popitem(last=False)


def _bytes_to_sound(audio_bytes: bytes) -> pygame.mixer.Sound | None:
    """Создаёт pygame.mixer.Sound из байтов (в памяти, без temp-файла)."""
    try:
        return pygame.mixer.Sound(io.BytesIO(audio_bytes))
    except Exception as ex:
        logger.bind(error=ex).warning("Не удалось загрузить аудио в pygame")
        return None


def _play_bytes(audio_bytes: bytes) -> None:
    """Воспроизводит аудио-байты через pygame (блокирующе)."""
    sound = _bytes_to_sound(audio_bytes)
    if sound is not None:
        _play_sound(sound)


def _play_sound(sound: pygame.mixer.Sound) -> None:
    """Воспроизводит Sound блокирующе."""
    try:
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
    except Exception as ex:
        logger.bind(error=ex).warning("Не удалось воспроизвести звук")


def preload_piper(*, wait: bool = False) -> None:
    """Предзагружает модель Piper (если провайдер активен).

    Args:
        wait: True — блокировать до завершения загрузки (для стартового бипа).
              False (по умолчанию) — загрузка в фоновом потоке.
    """
    providers = _active_providers()
    if piper_tts not in providers:
        return

    def _load() -> None:
        try:
            piper_tts.is_available()
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось предзагрузить Piper")

    thread = threading.Thread(target=_load, daemon=True)
    thread.start()
    if wait:
        thread.join()
