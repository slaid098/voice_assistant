import numpy as np
import pytest


def test_transcribe_success(monkeypatch):
    import speech_recognition as sr

    from voice_assistant.speech.providers.stt.google_stt import google_stt

    monkeypatch.setattr(sr.Recognizer, "recognize_google", lambda self, audio, **kw: "Привет мир")
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert google_stt.transcribe(audio) == "привет мир"


def test_transcribe_unknown_value(monkeypatch):
    import speech_recognition as sr

    from voice_assistant.speech.providers.stt.google_stt import google_stt

    def raise_unknown(self, audio, **kw):
        raise sr.UnknownValueError()

    monkeypatch.setattr(sr.Recognizer, "recognize_google", raise_unknown)
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert google_stt.transcribe(audio) is None


def test_transcribe_request_error(monkeypatch):
    import speech_recognition as sr

    from voice_assistant.speech.providers.stt.google_stt import STTNetworkError, google_stt

    def raise_error(self, audio, **kw):
        raise sr.RequestError("network")

    monkeypatch.setattr(sr.Recognizer, "recognize_google", raise_error)
    audio = np.array([0, 1, 2], dtype=np.int16)
    with pytest.raises(STTNetworkError):
        google_stt.transcribe(audio)


def test_transcribe_exception(monkeypatch):
    import speech_recognition as sr

    from voice_assistant.speech.providers.stt.google_stt import google_stt

    def raise_ex(self, audio, **kw):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(sr.Recognizer, "recognize_google", raise_ex)
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert google_stt.transcribe(audio) is None


def test_to_wav_bytes():
    from voice_assistant.speech.providers.stt.google_stt import _to_wav_bytes

    audio = np.array([0, 100, -100, 200], dtype=np.int16)
    wav = _to_wav_bytes(audio)
    assert isinstance(wav, bytes)
    assert len(wav) > 0
    assert wav[:4] == b"RIFF"


def test_transcribe_audio_facade_dispatches_google(monkeypatch):
    """Фасад transcribe_audio вызывает google_stt.transcribe при дефолте."""
    import voice_assistant.speech.stt as stt_mod

    called: list[bool] = []

    def fake_transcribe(audio):
        called.append(True)
        return "тест"

    monkeypatch.setattr(stt_mod.google_stt, "transcribe", fake_transcribe)
    monkeypatch.setattr(stt_mod.google_stt, "is_available", lambda: True)
    monkeypatch.setattr(stt_mod.vosk_stt, "is_available", lambda: False)

    audio = np.array([0, 1, 2], dtype=np.int16)
    result = stt_mod.transcribe_audio(audio)
    assert result == "тест"
    assert called == [True]


def test_transcribe_audio_fallback_to_vosk(monkeypatch):
    """При недоступности Google — fallback на Vosk."""
    import voice_assistant.speech.stt as stt_mod

    monkeypatch.setattr(stt_mod.google_stt, "is_available", lambda: False)
    monkeypatch.setattr(stt_mod.vosk_stt, "is_available", lambda: True)
    monkeypatch.setattr(stt_mod.vosk_stt, "transcribe", lambda audio: "vosk результат")

    audio = np.array([0, 1, 2], dtype=np.int16)
    assert stt_mod.transcribe_audio(audio) == "vosk результат"


def test_active_providers_vosk_mode(monkeypatch):
    """При STT_PROVIDER=vosk — Vosk первый, Google fallback."""
    import dataclasses

    import voice_assistant.speech.stt as stt_mod

    test_settings = dataclasses.replace(stt_mod.settings, stt_provider="vosk")
    monkeypatch.setattr(stt_mod, "settings", test_settings)

    providers = stt_mod._active_providers()
    assert providers[0] is stt_mod.vosk_stt
    assert providers[1] is stt_mod.google_stt
