import io
import wave

import numpy as np
import speech_recognition as sr
from loguru import logger

from voice_assistant.config import settings


class STTNetworkError(Exception):
    """Сетевая ошибка STT — интернет недоступен."""


_recognizer = sr.Recognizer()


def transcribe_audio(audio_data: np.ndarray) -> str | None:
    """Отправляет аудио в Google STT и возвращает распознанный текст.

    Args:
        audio_data: Numpy-массив аудио (int16, 16 kHz, mono).

    Returns:
        Текст в нижнем регистре или None при тишине (не распознано).

    Raises:
        STTNetworkError: при сетевой ошибке (нет интернета).
    """
    try:
        wav_bytes = _to_wav_bytes(audio_data)
        audio_item = sr.AudioData(wav_bytes, settings.samplerate, 2)
        text = _recognizer.recognize_google(audio_item, language="ru-RU")
        return str(text.lower().strip())
    except sr.UnknownValueError:
        return None
    except sr.RequestError as ex:
        logger.bind(error=ex).warning("STT: ошибка сети или таймаут")
        raise STTNetworkError("Нет связи с сервером распознавания") from ex
    except Exception as ex:
        logger.bind(error=ex, error_type=type(ex).__name__).error("STT: неожиданная ошибка")
        return None


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
