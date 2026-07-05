import io
import json
import wave
from importlib.resources import files
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from loguru import logger

from voice_assistant.config import settings

_MODEL_DIR: Path = Path(str(files("voice_assistant") / "assets" / "models" / "vosk"))


class VoskModelProtocol(Protocol):
    """Скрытый тип Model из vosk."""

    def recognizer(self, sample_rate: float, grammar: str | None = None) -> object: ...


class VoskRecognizerProtocol(Protocol):
    """Скрытый тип KaldiRecognizer из vosk."""

    def accept_waveform(self, data: bytes) -> int: ...

    def partial_result(self) -> str: ...

    def result(self) -> str: ...


class _ModelState:
    """Лениво загружает и хранит модель Vosk."""

    def __init__(self) -> None:
        self._model: VoskModelProtocol | None = None
        self._load_attempted = False

    def get(self) -> VoskModelProtocol | None:
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

            self._model = cast("VoskModelProtocol", Model(str(model_path)))
            logger.info(f"Модель Vosk загружена (офлайн-STT готов): {model_path}")
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось загрузить модель Vosk")

        return self._model


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
        model = _state.get()
        if model is None:
            raise RuntimeError("Vosk model not loaded")

        wav_bytes = _to_wav_bytes(audio)
        recognizer = cast("VoskRecognizerProtocol", model.recognizer(settings.samplerate))

        chunk_size = 4000
        text = ""
        for i in range(0, len(wav_bytes), chunk_size):
            chunk = wav_bytes[i : i + chunk_size]
            if recognizer.accept_waveform(chunk):
                result = json.loads(recognizer.result())
                text += result.get("text", "")

        result = json.loads(recognizer.result())
        text += result.get("text", "")

        text = text.strip().lower()
        return text or None

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель Vosk."""
        return _state.get() is not None


def _to_wav_bytes(audio_data: np.ndarray) -> bytes:
    """Конвертирует numpy-массив в WAV-байты."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(settings.samplerate)
        wf.writeframes(audio_data.tobytes())
    buf.seek(0)
    return buf.read()


vosk_stt = VoskSTTProvider()
