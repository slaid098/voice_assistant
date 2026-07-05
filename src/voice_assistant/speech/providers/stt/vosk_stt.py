import json
from importlib.resources import files
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from loguru import logger

from voice_assistant.config import settings

_MODEL_DIR: Path = Path(str(files("voice_assistant") / "assets" / "models" / "vosk"))


class VoskRecognizerProtocol(Protocol):
    """Скрытый тип KaldiRecognizer из vosk (CamelCase API)."""

    def AcceptWaveform(self, data: bytes) -> int: ...

    def PartialResult(self) -> str: ...

    def Result(self) -> str: ...

    def Reset(self) -> None: ...


class _ModelState:
    """Лениво загружает и хранит модель Vosk."""

    def __init__(self) -> None:
        self._model: object | None = None
        self._load_attempted = False

    def get(self) -> object | None:
        """Возвращает модель, загружая при первом обращении."""
        if self._model is not None or self._load_attempted:
            return self._model

        self._load_attempted = True
        model_path = _find_model_dir()
        if model_path is None:
            logger.warning("Модель Vosk не найдена, офлайн-STT недоступен")
            return None

        try:
            from vosk import Model  # noqa: PLC0415 — optional dependency

            self._model = Model(str(model_path))
            logger.info(f"Модель Vosk загружена (офлайн-STT готов): {model_path}")
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось загрузить модель Vosk")

        return self._model


def create_recognizer(grammar: str | None = None) -> VoskRecognizerProtocol | None:
    """Создаёт KaldiRecognizer из загруженной модели.

    Args:
        grammar: JSON-грамматика для ограничения словаря (None = полный словарь).

    Returns:
        KaldiRecognizer или None, если модель не загружена.
    """
    model = _state.get()
    if model is None:
        return None

    try:
        from vosk import KaldiRecognizer  # noqa: PLC0415 — optional dependency

        if grammar is not None:
            return cast(
                "VoskRecognizerProtocol",
                KaldiRecognizer(model, settings.samplerate, grammar),
            )
        return cast("VoskRecognizerProtocol", KaldiRecognizer(model, settings.samplerate))
    except Exception as ex:
        logger.bind(error=ex).warning("Не удалось создать KaldiRecognizer")
        return None


def _find_model_dir() -> Path | None:
    """Находит директорию модели Vosk (поддерживает распакованные архивы)."""
    if not _MODEL_DIR.exists():
        return None
    for child in _MODEL_DIR.iterdir():
        if child.is_dir() and child.name.startswith("vosk-model"):
            return child
    return None


_state = _ModelState()


class VoskSTTProvider:
    """Офлайн STT через Vosk. Local-провайдер, мгновенно без сети.

    Использует полный словарь (без грамматики) для распознавания свободной речи.
    Для wake-word детекции есть отдельный VoskWakeWordDetector (грамматика).
    """

    name = "vosk"
    is_cloud = False

    def transcribe(self, audio: np.ndarray) -> str | None:
        """Распознаёт речь через Vosk (полный словарь).

        Args:
            audio: Numpy-массив аудио (int16, 16 kHz, mono).

        Returns:
            Текст в нижнем регистре или None при тишине (не распознано).
        """
        recognizer = create_recognizer()
        if recognizer is None:
            raise RuntimeError("Vosk model not loaded")

        raw_pcm = audio.tobytes()

        chunk_size = 4000
        text = ""
        for i in range(0, len(raw_pcm), chunk_size):
            chunk = raw_pcm[i : i + chunk_size]
            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                text += result.get("text", "")

        result = json.loads(recognizer.Result())
        text += result.get("text", "")

        text = text.strip().lower()
        return text or None

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель Vosk."""
        return _state.get() is not None


vosk_stt = VoskSTTProvider()
