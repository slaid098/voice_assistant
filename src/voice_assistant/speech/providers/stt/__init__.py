"""STT-провайдеры (распознавание речи)."""

from voice_assistant.speech.providers.stt.base import STTProvider
from voice_assistant.speech.providers.stt.google_stt import google_stt
from voice_assistant.speech.providers.stt.vosk_stt import vosk_stt

__all__ = ["STTProvider", "google_stt", "vosk_stt"]
