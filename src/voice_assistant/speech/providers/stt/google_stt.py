import io
import wave

import numpy as np
import speech_recognition as sr
from loguru import logger

from voice_assistant.config import settings


class STTNetworkError(Exception):
    """Сетевая ошибка STT — интернет недоступен."""


class GoogleSTTProvider:
    """Онлайн STT через Google Web Speech (SpeechRecognition). Основной cloud-провайдер.

    Требует интернет. При сетевой ошибке поднимает STTNetworkError.
    """

    name = "google"
    is_cloud = True

    def __init__(self) -> None:
        self._recognizer = sr.Recognizer()

    def transcribe(self, audio: np.ndarray) -> str | None:
        """Распознаёт речь через Google STT.

        Args:
            audio: Numpy-массив аудио (int16, 16 kHz, mono).

        Returns:
            Текст в нижнем регистре или None при тишине (не распознано).

        Raises:
            STTNetworkError: при сетевой ошибке (нет интернета).
        """
        try:
            wav_bytes = _to_wav_bytes(audio)
            audio_item = sr.AudioData(wav_bytes, settings.samplerate, 2)
            text = self._recognizer.recognize_google(audio_item, language=settings.stt_language)
            return str(text.lower().strip())
        except sr.UnknownValueError:
            return None
        except sr.RequestError as ex:
            logger.bind(error=ex).warning("Распознавание речи: ошибка сети или таймаут")
            raise STTNetworkError("Нет связи с сервером распознавания") from ex
        except Exception as ex:
            logger.bind(error=ex, error_type=type(ex).__name__).error(
                "Распознавание речи: неожиданная ошибка"
            )
            return None

    def is_available(self) -> bool:
        """Google STT всегда «доступен» — сеть проверяется при самом распознавании."""
        return True


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


google_stt = GoogleSTTProvider()
