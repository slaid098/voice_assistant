from typing import Protocol


class TTSProvider(Protocol):
    """Интерфейс движка текст-в-речь (plug-in точка для замены)."""

    def synthesize(self, text: str) -> bytes:
        """Синтезирует текст в WAV-байты (16-bit PCM, mono).

        Args:
            text: Текст для озвучки.

        Returns:
            WAV-байты.

        Raises:
            Exception: если синтез не удался.
        """
        ...

    def is_available(self) -> bool:
        """Проверяет, готов ли провайдер к работе."""
        ...
