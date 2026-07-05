from collections.abc import Callable

import numpy as np
import sounddevice as sd
from loguru import logger

from voice_assistant.config import settings


def record_user_speech(
    timeout_ms: int, *, on_chunk: Callable[[np.ndarray], None] | None = None
) -> np.ndarray | None:
    """Записывает речь с микрофона до silence_limit_ms тишины.

    Если задан on_chunk — каждый чанк передаётся в колбэк параллельно с VAD.
    Нужно для стриминговых детекторов (Vosk wake word, openWakeWord).

    Args:
        timeout_ms: Максимум ожидания начала речи (мс). При таймауте — None.
        on_chunk: Колбэк для стриминговых детекторов (необязательно).

    Returns:
        Аудио-массив или None при таймауте (молчание).
    """
    chunk_size = int(settings.chunk_ms * settings.samplerate / 1000)
    buffer: list[np.ndarray] = []
    silence_ms = 0
    total_elapsed_ms = 0
    active_speech_started = False

    logger.debug("[запись] Слушаю...")
    with sd.InputStream(samplerate=settings.samplerate, channels=1, dtype="int16") as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()

            if on_chunk is not None:
                on_chunk(chunk)

            is_voice_detected = _is_voice(chunk)

            if is_voice_detected:
                active_speech_started = True
                silence_ms = 0
                buffer.append(chunk)
            elif active_speech_started:
                silence_ms += settings.chunk_ms
                buffer.append(chunk)
                if silence_ms >= settings.silence_limit_ms:
                    break
            else:
                total_elapsed_ms += settings.chunk_ms
                if total_elapsed_ms >= timeout_ms:
                    logger.debug("[запись] Время ожидания истекло (тишина).")
                    return None

    logger.debug("[запись] Запись завершена.")
    return np.concatenate(buffer) if buffer else None


def _rms(samples: np.ndarray) -> float:
    """Вычисляет AC RMS (вычитая DC Offset)."""
    samples_clean = samples.astype(np.float64)
    if samples_clean.size == 0:
        return 0.0
    std_val = float(np.std(samples_clean))
    if std_val > 1e-9:
        return std_val
    return float(np.sqrt(np.mean(samples_clean**2)))


def _is_voice(chunk: np.ndarray) -> bool:
    """Проверяет, есть ли голос выше порога."""
    return _rms(chunk) > settings.vad_threshold
