import io
import socket

import gtts


class GoogleTTSProvider:
    """Онлайн TTS через Google (gTTS). Основной провайдер."""

    def synthesize(self, text: str) -> bytes:
        """Синтезирует текст через gTTS, возвращает MP3-байты.

        Args:
            text: Текст для озвучки.

        Returns:
            MP3-байты.

        Raises:
            Exception: при сетевой ошибке / недоступности Google.
        """
        mp3_bytes = io.BytesIO()
        tts = gtts.gTTS(text, lang="ru", slow=False, lang_check=False)
        tts.write_to_fp(mp3_bytes)
        mp3_bytes.seek(0)
        return mp3_bytes.getvalue()

    def is_available(self) -> bool:
        """Проверяет доступность Google TTS (без полноценного запроса)."""
        try:
            socket.gethostbyname("translate.google.com")
        except Exception:
            return False
        else:
            return True


google_tts = GoogleTTSProvider()
