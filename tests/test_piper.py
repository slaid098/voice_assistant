import pytest


def test_piper_synthesize_returns_wav(monkeypatch):
    """PiperTTSProvider.synthesize returns WAV bytes."""
    import voice_assistant.speech.providers.piper_tts as piper_mod

    if not piper_mod.piper_tts.is_available():
        pytest.skip("Piper model not available in this environment")

    wav = piper_mod.piper_tts.synthesize("Привет")
    assert isinstance(wav, bytes)
    assert wav[:4] == b"RIFF"
    assert len(wav) > 44  # WAV header + data


def test_piper_not_available_when_model_missing(monkeypatch):
    """PiperTTSProvider returns None when model file doesn't exist."""
    from pathlib import Path

    import voice_assistant.speech.providers.piper_tts as piper_mod

    monkeypatch.setattr(piper_mod, "_VOICE_MODEL", Path("/nonexistent/model.onnx"))
    monkeypatch.setattr(piper_mod, "_VOICE_CONFIG", Path("/nonexistent/model.json"))
    monkeypatch.setattr(piper_mod._state, "_voice", None)
    monkeypatch.setattr(piper_mod._state, "_load_attempted", False)

    provider = piper_mod.PiperTTSProvider()
    assert provider.is_available() is False


def test_piper_synthesize_raises_when_not_loaded():
    """PiperTTSProvider.synthesize raises when model not loaded."""
    from voice_assistant.speech.providers.piper_tts import PiperTTSProvider

    provider = PiperTTSProvider()
    if provider.is_available():
        pytest.skip("Model is loaded, can't test failure path")

    with pytest.raises(RuntimeError, match="not loaded"):
        provider.synthesize("test")
