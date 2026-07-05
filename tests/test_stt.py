import numpy as np
import pytest


def test_transcribe_success(monkeypatch):
    import voice_assistant.speech.stt as stt_mod

    monkeypatch.setattr(stt_mod._recognizer, "recognize_google", lambda audio, **kw: "Привет мир")
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert stt_mod.transcribe_audio(audio) == "привет мир"


def test_transcribe_unknown_value(monkeypatch):
    import speech_recognition as sr

    import voice_assistant.speech.stt as stt_mod

    def raise_unknown(audio, **kw):
        raise sr.UnknownValueError()

    monkeypatch.setattr(stt_mod._recognizer, "recognize_google", raise_unknown)
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert stt_mod.transcribe_audio(audio) is None


def test_transcribe_request_error(monkeypatch):
    import speech_recognition as sr

    import voice_assistant.speech.stt as stt_mod
    from voice_assistant.speech.stt import STTNetworkError

    def raise_error(audio, **kw):
        raise sr.RequestError("network")

    monkeypatch.setattr(stt_mod._recognizer, "recognize_google", raise_error)
    audio = np.array([0, 1, 2], dtype=np.int16)
    with pytest.raises(STTNetworkError):
        stt_mod.transcribe_audio(audio)


def test_transcribe_exception(monkeypatch):
    import voice_assistant.speech.stt as stt_mod

    def raise_ex(audio, **kw):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(stt_mod._recognizer, "recognize_google", raise_ex)
    audio = np.array([0, 1, 2], dtype=np.int16)
    assert stt_mod.transcribe_audio(audio) is None


def test_to_wav_bytes():
    from voice_assistant.speech.stt import _to_wav_bytes

    audio = np.array([0, 100, -100, 200], dtype=np.int16)
    wav = _to_wav_bytes(audio)
    assert isinstance(wav, bytes)
    assert len(wav) > 0
    assert wav[:4] == b"RIFF"
