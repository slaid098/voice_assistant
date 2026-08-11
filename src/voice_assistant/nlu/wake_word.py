"""Детекция слова активации (wake word) через openWakeWord.

Единственный детектор — openWakeWord (нейросетевой, ONNX).
Стримит чанки аудио в реальном времени, возвращает wake word при детекции.
Модель wiki.onnx обучена на Vast.ai (FP/hour=0.0, recall 26%).
"""

from typing import Any, Protocol

import numpy as np
from loguru import logger

from voice_assistant.config import settings
from voice_assistant.speech.model_loader import resolve_openwakeword_model


class WakeWordDetector(Protocol):
    """Интерфейс детектора слова активации.

    Аудио-стриминговые детекторы реализуют detect_chunk(): питаются чанками
    в реальном времени и возвращают распознанное слово при детекции.
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

    def reset(self) -> None:
        """Очищает внутреннее состояние между wake-сессиями."""
        ...


class OpenWakeWordDetector:
    """Нейросетевой детектор слова активации на openWakeWord (ONNX).

    Стримит чанки аудио (int16, 16kHz) в openWakeWord Model.predict().
    Буферизует входящие чанки по 1280 samples (80ms) — стандарт openWakeWord.
    При score >= 0.5 возвращает settings.wake_word.
    """

    name = "openwakeword"
    _threshold = 0.5
    _feed_size = 1280  # 80ms at 16kHz — стандартный размер чанка openWakeWord
    _buf_capacity = 4096  # pre-allocated buffer (no per-chunk realloc)

    def __init__(self) -> None:
        self._model: Any = None
        self._buffer: np.ndarray = np.zeros(self._buf_capacity, dtype=np.int16)
        self._buf_len: int = 0

        model_path = resolve_openwakeword_model()
        if not model_path.exists():
            logger.warning(f"Модель openWakeWord не найдена: {model_path}")
            return

        try:
            from openwakeword.model import Model  # noqa: PLC0415 — optional dependency

            self._model = Model(wakeword_models=[str(model_path)])
            logger.info(f"openWakeWord детектор готов: {model_path}")
        except Exception as ex:
            logger.bind(error=ex).opt(exception=True).warning(
                "Не удалось загрузить модель openWakeWord"
            )

    def reset(self) -> None:
        """Очищает буфер и внутреннее состояние модели между wake-сессиями."""
        self._buffer.fill(0)
        self._buf_len = 0
        if self._model is not None and hasattr(self._model, "reset"):
            self._model.reset()

    def detect_chunk(self, chunk: np.ndarray) -> str | None:
        """Обрабатывает чанк аудио, возвращает wake word при детекции.

        Буферизует входящие чанки в pre-allocated массив (без realloc каждый
        чанк), кормит openWakeWord по 1280 samples (80ms).
        При score >= 0.5 возвращает settings.wake_word.

        Args:
            chunk: Numpy-массив аудио (int16, 16 kHz, mono).

        Returns:
            Wake word или None (продолжаем слушать).
        """
        if self._model is None:
            return None

        n = len(chunk)
        if n > self._buffer.size:
            chunk = chunk[-self._buffer.size :]
            n = len(chunk)
        if self._buf_len + n > self._buffer.size:
            self._buf_len = 0
        self._buffer[self._buf_len : self._buf_len + n] = chunk
        self._buf_len += n

        while self._buf_len >= self._feed_size:
            feed = self._buffer[: self._feed_size].copy()
            self._buf_len -= self._feed_size
            if self._buf_len > 0:
                self._buffer[: self._buf_len] = self._buffer[
                    self._feed_size : self._feed_size + self._buf_len
                ]
            scores: dict[str, float] = self._model.predict(feed)
            if not scores:
                continue
            score = max(scores.values())
            if score >= self._threshold:
                return settings.wake_word

        return None

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель openWakeWord."""
        return self._model is not None


_cached_detector: OpenWakeWordDetector | None = None
_load_failed: bool = False


def active_wake_word_detector() -> WakeWordDetector | None:
    """Возвращает детектор согласно настройке WAKE_WORD_DETECTOR.

    openwakeword → OpenWakeWordDetector (если доступен, иначе None).
    Детектор кэшируется на уровне модуля — создаётся один раз при первом
    вызове (или через preload_wake_word_detector при старте), чтобы не
    пересоздавать ONNX-модель (~1-2s) на каждом цикле прослушивания.
    При неудачной загрузке failure кэшируется (_load_failed) — повторные
    вызовы возвращают None без retry, чтобы не плодить ошибки в цикле.
    """
    global _cached_detector, _load_failed  # noqa: PLW0603 — module-level singleton pattern

    if _cached_detector is not None:
        return _cached_detector
    if _load_failed:
        return None

    if settings.wake_word_detector == "openwakeword":
        detector = OpenWakeWordDetector()
        if detector.is_available():
            _cached_detector = detector
            return detector
        _load_failed = True
        logger.error("openWakeWord детектор недоступен — модель не загружена")
        return None

    logger.error(f"Неизвестный детектор: {settings.wake_word_detector}")
    return None


def preload_wake_word_detector() -> None:
    """Предзагружает модель wake-word детектора при старте.

    Загружает openWakeWord модель при старте и кэширует её, чтобы первый
    wake word не задерживался и модель не пересоздавалась между циклами.
    """
    detector = active_wake_word_detector()
    if detector is not None:
        logger.info(f"Wake-word детектор готов: {detector.name}")
