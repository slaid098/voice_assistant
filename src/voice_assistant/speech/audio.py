import numpy as np
import sounddevice as sd

from voice_assistant.config import CHUNK_MS, SAMPLERATE

_VAD_THRESHOLD = 200.0
_SILENCE_LIMIT_MS = 1800
_RMS_EPSILON = 1e-9


def record_user_speech(timeout_ms: int = 6000) -> np.ndarray | None:
    """Записывает речь с микрофона до 1.8 секунд тишины.

    Если речь не началась в течение timeout_ms — возвращает None.
    """
    chunk_size = int(CHUNK_MS * SAMPLERATE / 1000)
    buffer = []
    silence_ms = 0
    total_elapsed_ms = 0
    active_speech_started = False

    print("[VAD] Слушаю...")
    with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype="int16") as stream:
        while True:
            chunk, _ = stream.read(chunk_size)
            chunk = chunk.flatten()

            is_voice_detected = _is_voice(chunk)

            if is_voice_detected:
                active_speech_started = True
                silence_ms = 0
                buffer.append(chunk)
            elif active_speech_started:
                silence_ms += CHUNK_MS
                buffer.append(chunk)
                if silence_ms >= _SILENCE_LIMIT_MS:
                    break
            else:
                total_elapsed_ms += CHUNK_MS
                if total_elapsed_ms >= timeout_ms:
                    print("[VAD] Время ожидания истекло (тишина).")
                    return None

    print("[VAD] Запись завершена.")
    return np.concatenate(buffer) if buffer else None


def _rms(samples: np.ndarray) -> float:
    """Вычисляет AC RMS (вычитая DC Offset)."""
    samples_clean = samples.astype(np.float64)
    if samples_clean.size == 0:
        return 0.0
    std_val = float(np.std(samples_clean))
    if std_val > _RMS_EPSILON:
        return std_val
    return float(np.sqrt(np.mean(samples_clean**2)))


def _is_voice(chunk: np.ndarray) -> bool:
    """Проверяет, есть ли голос выше порога."""
    return _rms(chunk) > _VAD_THRESHOLD