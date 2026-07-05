from typing import Protocol

import numpy as np


class STTProvider(Protocol):
    """Интерфейс движка распознавания речи (plug-in точка для замены).

    Классификация провайдеров по типу (как TTSProvider):
      - is_cloud=True  — сетевое распознавание (Google, Яндекс, Azure): дорогой
        запрос, может поднять STTNetworkError при отсутствии интернета.
      - is_cloud=False — локальное распознавание (Vosk, whisper.cpp): мгновенное,
        без сети, не падает по сети.
    """

    name: str
    is_cloud: bool

    def transcribe(self, audio: np.ndarray) -> str | None:
        """Распознаёт речь из аудио-массива.

        Args:
            audio: Numpy-массив аудио (int16, 16 kHz, mono).

        Returns:
            Текст в нижнем регистре или None при тишине/неудаче.

        Raises:
            STTNetworkError: при сетевой ошибке (только cloud-провайдеры).
        """
        ...

    def is_available(self) -> bool:
        """Проверяет, готов ли провайдер к работе (модель загружена / сеть есть)."""
        ...
