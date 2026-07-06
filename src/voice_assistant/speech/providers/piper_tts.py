import io
import wave
from collections.abc import Iterator
from typing import Protocol, cast

from loguru import logger

from voice_assistant.speech.mixer import ensure_mixer as _ensure_mixer
from voice_assistant.speech.model_loader import piper_config_path, piper_model_path

_VOICE_MODEL = piper_model_path()
_VOICE_CONFIG = piper_config_path()


class PiperAudioChunk(Protocol):
    """Скрытый тип AudioChunk из piper."""

    audio_int16_bytes: bytes


class PiperVoiceProtocol(Protocol):
    """Скрытый тип PiperVoice из piper."""

    def synthesize(self, text: str) -> Iterator[PiperAudioChunk]: ...


class _VoiceState:
    """Лениво загружает и хранит модель Piper."""

    def __init__(self) -> None:
        self._voice: PiperVoiceProtocol | None = None
        self._load_attempted = False

    def get(self) -> PiperVoiceProtocol | None:
        """Возвращает модель, загружая при первом обращении."""
        if self._voice is not None or self._load_attempted:
            return self._voice

        self._load_attempted = True

        if not _VOICE_MODEL.exists() or not _VOICE_CONFIG.exists():
            logger.warning("Модель Piper не найдена, офлайн-TTS недоступен")
            return None

        try:
            _ensure_mixer()
            from piper import PiperVoice  # noqa: PLC0415 — optional dependency

            self._voice = cast(
                "PiperVoiceProtocol",
                PiperVoice.load(str(_VOICE_MODEL), config_path=str(_VOICE_CONFIG)),
            )
            logger.info("Модель Piper загружена (офлайн-TTS готов)")
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось загрузить модель Piper")

        return self._voice


_state = _VoiceState()


class PiperTTSProvider:
    """Офлайн TTS через Piper (ONNX, CPU). Fallback при недоступности Google.

    is_cloud=False — локальный синтез мгновенный, кэширование не применяется.
    fixed_phrase() всегда возвращает None: локальный провайдер синтезирует
    на лету, предгенерированные MP3 от Google не используются (другой голос).
    """

    name = "piper"
    is_cloud = False

    def __init__(self) -> None:
        self._voice: PiperVoiceProtocol | None = None

    def _ensure_loaded(self) -> PiperVoiceProtocol | None:
        if self._voice is None:
            self._voice = _state.get()
        return self._voice

    def synthesize(self, text: str) -> bytes:
        """Синтезирует текст через Piper ONNX, возвращает WAV-байты.

        Args:
            text: Текст для озвучки.

        Returns:
            WAV-байты (16-bit PCM, mono, 22050 Hz).

        Raises:
            RuntimeError: если модель не загружена.
        """
        voice = self._ensure_loaded()
        if voice is None:
            raise RuntimeError("Piper voice model not loaded")

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            for chunk in voice.synthesize(text):
                wf.writeframes(chunk.audio_int16_bytes)
        buf.seek(0)
        return buf.read()

    def is_available(self) -> bool:
        """Проверяет, загружена ли модель Piper."""
        return self._ensure_loaded() is not None

    def fixed_phrase(self, text: str) -> bytes | None:
        """Локальный провайдер не использует предгенерированные фразы."""
        return None


piper_tts = PiperTTSProvider()
