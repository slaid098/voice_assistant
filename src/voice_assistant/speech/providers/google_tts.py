import io
import socket
import time
from importlib.resources import files
from json import loads as _json_loads
from pathlib import Path

import gtts
from loguru import logger

_AVAILABLE_TTL_SEC: float = 60.0
_PHRASES_DIR: Path = Path(str(files("voice_assistant") / "assets" / "sounds" / "phrases"))
_MANIFEST_PATH: Path = _PHRASES_DIR / "manifest.json"


class _ManifestState:
    """Лениво загружает и хранит manifest.json (один раз)."""

    def __init__(self) -> None:
        self._manifest: dict[str, str] | None = None
        self._load_attempted = False

    def get(self) -> dict[str, str]:
        """Возвращает маппинг текст→файл, загружая при первом обращении."""
        if self._manifest is not None or self._load_attempted:
            return self._manifest or {}

        self._load_attempted = True
        if not _MANIFEST_PATH.exists():
            self._manifest = {}
            return self._manifest

        try:
            self._manifest = _json_loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception as ex:
            logger.bind(error=ex).warning("Не удалось прочитать manifest.json")
            self._manifest = {}
        return self._manifest


_manifest_state = _ManifestState()


class GoogleTTSProvider:
    """Онлайн TTS через Google (gTTS). Основной cloud-провайдер.

    Кэшируется в LRU-кэше динамики. Фиксированные фразы — из ассетов
    (assets/sounds/phrases/*.mp3 через manifest.json).
    """

    name = "google"
    is_cloud = True

    def __init__(self) -> None:
        self._available_cache: bool | None = None
        self._available_checked_at: float = 0.0

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
        """Проверяет доступность Google TTS с кэшированием на _AVAILABLE_TTL_SEC.

        DNS-lookup выполняется не чаще раза в минуту, чтобы не тормозить
        каждый вызов speak().
        """
        now = time.monotonic()
        cached = self._available_cache
        if cached is not None and (now - self._available_checked_at) < _AVAILABLE_TTL_SEC:
            return cached

        try:
            socket.gethostbyname("translate.google.com")
        except Exception:
            self._available_cache = False
        else:
            self._available_cache = True
        self._available_checked_at = now
        return self._available_cache

    def fixed_phrase(self, text: str) -> bytes | None:
        """Возвращает предгенерированные MP3-байты из ассетов для фиксированной фразы.

        Args:
            text: Текст фиксированной фразы (точное совпадение).

        Returns:
            MP3-байты из assets/sounds/phrases/ или None, если фраза не найдена.
        """
        manifest = _manifest_state.get()
        filename = manifest.get(text)
        if filename is None:
            return None
        path = _PHRASES_DIR / filename
        if not path.exists():
            logger.warning(f"Файл фиксированной фразы не найден: {path}")
            return None
        return path.read_bytes()


google_tts = GoogleTTSProvider()
