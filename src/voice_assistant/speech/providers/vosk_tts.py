"""Офлайн TTS через Vosk (ONNX, без torch).

Модель: vosk-model-tts-ru-0.7-multi (~135 МБ, 5 спикеров).
Спикер #2 = «irina» (женский голос, по умолчанию).

Зависимости: vosk-tts, onnxruntime (общий с Piper).
Модель скачивается автоматически библиотекой при первом использовании,
если отсутствует в models/vosk_tts/.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import Protocol, cast

from loguru import logger

from voice_assistant.config import settings
from voice_assistant.speech.model_loader import vosk_tts_model_path

_SAMPLE_RATE = 22050


class VoskTTSModelProtocol(Protocol):
    """Скрытый тип Model из vosk_tts."""

    def get_model_path(self) -> Path: ...

    def get_model_by_name(self, name: str) -> Path: ...


class VoskSynthProtocol(Protocol):
    """Скрытый тип Synth из vosk_tts."""

    def synth_audio(self, text: str, speaker_id: int = 0) -> object: ...


class _ModelState:
    """Лениво загружает и хранит модель Vosk TTS."""

    def __init__(self) -> None:
        self._model: VoskTTSModelProtocol | None = None
        self._synth: VoskSynthProtocol | None = None
        self._load_attempted = False

    def get_synth(self) -> VoskSynthProtocol | None:
        """Возвращает Synth, загружая модель при первом обращении."""
        if self._synth is not None or self._load_attempted:
            return self._synth

        self._load_attempted = True

        try:
            from vosk_tts import Model, Synth  # noqa: PLC0415 — optional dependency

            local_path = vosk_tts_model_path()
            if local_path.exists() and any(local_path.iterdir()):
                model = cast("VoskTTSModelProtocol", Model(model_path=local_path))
                logger.info(f"Модель Vosk TTS загружена локально: {local_path}")
            else:
                model = cast(
                    "VoskTTSModelProtocol",
                    Model(model_name=settings.vosk_tts_model),
                )
                logger.info("Модель Vosk TTS загружена (авто-скачивание)")

            self._model = model
            self._synth = cast("VoskSynthProtocol", Synth(model))
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось загрузить модель Vosk TTS")

        return self._synth


_state = _ModelState()


def preload_vosk_tts() -> None:
    """Предзагружает модель Vosk TTS при старте.

    Если модель в models/vosk_tts/ — загружает локально (~1-2 сек).
    Если нет — авто-скачивание (~135 МБ, 30-60 сек).
    """
    _state.get_synth()


class VoskTTSProvider:
    """Офлайн TTS через Vosk (ONNX, без torch).

    is_cloud=False — локальный синтез, мгновенно без сети.
    5 спикеров, по умолчанию #2 «irina» (женский).
    """

    name = "vosk"
    is_cloud = False

    def synthesize(self, text: str) -> bytes:
        """Синтезирует текст через Vosk TTS, возвращает WAV-байты.

        Args:
            text: Текст для озвучки.

        Returns:
            WAV-байты (16-bit PCM, mono, 22050 Hz).

        Raises:
            RuntimeError: если модель не загружена.
        """
        synth = _state.get_synth()
        if synth is None:
            raise RuntimeError("Vosk TTS model not loaded")

        audio = synth.synth_audio(text, speaker_id=settings.vosk_tts_speaker)
        audio_bytes = _to_wav_bytes(audio)

        return audio_bytes

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель Vosk TTS."""
        return _state.get_synth() is not None

    def fixed_phrase(self, text: str) -> bytes | None:
        """Локальный провайдер не использует предгенерированные фразы."""
        return None


def _to_wav_bytes(audio: object) -> bytes:
    """Конвертирует numpy array в WAV-байты."""
    import numpy as np  # noqa: PLC0415 — numpy already a dependency

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(np.asarray(audio, dtype=np.int16).tobytes())
    buf.seek(0)
    return buf.read()


vosk_tts = VoskTTSProvider()
