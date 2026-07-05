"""Детекция слова активации (wake word).

Два типа детекторов:
  - fuzzy (текстовый): запись→распознание→fuzzy-матчинг. Текущий путь (Google STT).
  - vosk (аудио-стрим): Vosk-грамматика узким списком→fuzzy-порог. Мгновенно локально.

WakeWordDetector Protocol — точка расширения для будущих детекторов
(openWakeWord, и т.д.).
"""

import json
from typing import Protocol, cast

import numpy as np
from loguru import logger
from thefuzz import fuzz

from voice_assistant.config import settings


class VoskRecognizerProtocol(Protocol):
    """Скрытый тип KaldiRecognizer из vosk."""

    def accept_waveform(self, data: bytes) -> int: ...

    def partial_result(self) -> str: ...

    def result(self) -> str: ...


class WakeWordDetector(Protocol):
    """Интерфейс детектора слова активации.

    Аудио-стриминговые детекторы (Vosk, openWakeWord) реализуют detect_chunk():
    питаются чанками в реальном времени и возвращают распознанное слово при детекции.
    """

    name: str

    def detect_chunk(self, chunk: np.ndarray) -> str | None:
        """Обрабатывает чанк аудио, возвращает wake word при детекции.

        Args:
            chunk: Numpy-массив аудио (int16, 16 kHz, mono).

        Returns:
            Распознанное слово или None (продолжаем слушать).
        """
        ...

    def is_available(self) -> bool:
        """Проверяет, готов ли детектор к работе (модель загружена)."""
        ...


def is_wake_word(text: str) -> bool:
    """Проверяет, содержит ли фраза слово активации (fuzzy-матчинг).

    Сохраняется для fuzzy-пути (Google STT → текст → проверка).

    Args:
        text: Распознанная фраза пользователя.

    Returns:
        True, если слово активации найдено.
    """
    if not text:
        return False

    words = text.lower().strip().split()
    return any(_matches_wake_word(word) for word in words)


def _matches_wake_word(word: str) -> bool:
    """Проверяет одно слово против wake word и алиасов."""
    if settings.wake_word in word:
        return True

    for alias in settings.wake_aliases:
        if alias in word:
            return True
        if fuzz.ratio(alias, word) >= settings.wake_threshold:
            return True

    root = settings.wake_word[:3] if len(settings.wake_word) >= 3 else settings.wake_word
    return root in word


class FuzzyWakeWordDetector:
    """Текстовый fuzzy-детектор. Обёртка над is_wake_word для Google-пути.

    Аудио здесь не стримится — детекция идёт после полного распознавания Google.
    detect_chunk копит чанки, но реальную проверку делает только в конце
    (через _finalize_and_check). Это заглушка-адаптер для единого интерфейса.
    """

    name = "fuzzy"

    def __init__(self) -> None:
        self._buffer: list[np.ndarray] = []

    def detect_chunk(self, chunk: np.ndarray) -> str | None:
        """Копит чанки. Реальная детекция — после распознавания Google."""
        self._buffer.append(chunk)
        return None

    def is_available(self) -> bool:
        """Fuzzy-детектор всегда доступен (не требует модели)."""
        return True


class VoskWakeWordDetector:
    """Аудио-стриминговый детектор на Vosk-грамматике.

    Узкая грамматика ['вики','вика','ники','мики','[unk]'] (из wake_aliases) +
    fuzzy-порог (fuzz.ratio >= WAKE_THRESHOLD) для отсечения ложных срабатываний.
    Мгновенно локально, без сети.
    """

    name = "vosk"

    def __init__(self) -> None:
        self._recognizer: VoskRecognizerProtocol | None = None
        self._load_attempted = False

    def _ensure_loaded(self) -> object | None:
        """Лениво создаёт KaldiRecognizer с грамматикой из wake_aliases."""
        if self._recognizer is not None or self._load_attempted:
            return self._recognizer

        self._load_attempted = True
        from voice_assistant.speech.providers.stt.vosk_stt import (  # noqa: PLC0415
            _state as vosk_state,
        )

        model = vosk_state.get()
        if model is None:
            logger.warning("Vosk wake-word детектор недоступен (модель не загружена)")
            return None

        grammar = _build_grammar()
        try:
            self._recognizer = cast(
                "VoskRecognizerProtocol", model.recognizer(settings.samplerate, grammar)
            )
            logger.info("Vosk wake-word детектор готов (грамматика + fuzzy-порог)")
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось создать Vosk wake-word recognizer")

        return self._recognizer

    def detect_chunk(self, chunk: np.ndarray) -> str | None:
        """Обрабатывает чанк, возвращает wake word при детекции.

        Двойная защита от ложных срабатываний:
        1. Vosk-грамматика отдаёт только слова из списка
        2. fuzzy-порог (fuzz.ratio >= WAKE_THRESHOLD) отсекает неточные совпадения
        """
        recognizer = self._ensure_loaded()
        if recognizer is None:
            return None

        raw_bytes = chunk.tobytes()
        rec = cast("VoskRecognizerProtocol", recognizer)
        if rec.accept_waveform(raw_bytes):
            result = json.loads(rec.result())
            text = result.get("text", "").strip().lower()
            return _check_wake_word_fuzzy(text)

        partial = json.loads(rec.partial_result())
        text = partial.get("partial", "").strip().lower()
        return _check_wake_word_fuzzy(text)

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель Vosk."""
        return self._ensure_loaded() is not None


def _build_grammar() -> str:
    """Собирает JSON-грамматику из wake_aliases для Vosk.

    Формат: '["вики", "вика", "ники", "[unk]"]' — Vosk распознаёт только эти слова.
    """
    words = [*list(settings.wake_aliases), "[unk]"]
    unique = list(dict.fromkeys(words))

    return json.dumps(unique, ensure_ascii=False)


def _check_wake_word_fuzzy(text: str) -> str | None:
    """Проверяет распознанный текст через fuzzy-порог.

    Returns:
        Распознанное слово (если проходит порог) или None.
    """
    if not text or text == "[unk]":
        return None

    words = text.split()
    for word in words:
        if settings.wake_word in word:
            return word
        for alias in settings.wake_aliases:
            if alias in word or fuzz.ratio(alias, word) >= settings.wake_threshold:
                return word

    return None


def active_wake_word_detector() -> WakeWordDetector | None:
    """Возвращает детектор согласно настройке WAKE_WORD_DETECTOR.

    vosk → VoskWakeWordDetector (если доступен, иначе None → fallback на fuzzy)
    fuzzy → FuzzyWakeWordDetector
    """
    if settings.wake_word_detector == "vosk":
        detector = VoskWakeWordDetector()
        if detector.is_available():
            return detector
        logger.warning("Vosk wake-word недоступен, авто-fallback на fuzzy")
        return None
    return FuzzyWakeWordDetector()
