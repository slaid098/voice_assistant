import numpy as np
import sounddevice as sd

from voice_assistant.config import settings


def record_user_speech(timeout_ms: int = 6000) -> np.ndarray | None:
    """Записывает речь с микрофона до silence_limit_ms тишины.

    Если речь не началась в течение timeout_ms — возвращает None.
    """
    chunk_size = int(settings.chunk_ms * settings.samplerate / 1000)
    buffer = []
    silence_ms = 0
    total_elapsed_ms = 0
    active_speech_started = False

    print("[запись] Слушаю...")
    with sd.InputStream(samplerate=settings.samplerate, channels=1, dtype="int16") as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()

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
                    print("[запись] Время ожидания истекло (тишина).")
                    return None

    print("[запись] Запись завершена.")
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
