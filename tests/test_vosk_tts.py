"""Тесты VoskTTSProvider."""


def test_vosk_tts_provider_properties():
    """Проверка статических свойств провайдера."""
    from voice_assistant.speech.providers.vosk_tts import VoskTTSProvider

    provider = VoskTTSProvider()
    assert provider.name == "vosk"
    assert provider.is_cloud is False


def test_vosk_tts_fixed_phrase_returns_none():
    """Локальный провайдер не имеет предгенерированных фраз."""
    from voice_assistant.speech.providers.vosk_tts import VoskTTSProvider

    provider = VoskTTSProvider()
    assert provider.fixed_phrase("любой текст") is None


def test_vosk_tts_synthesize_raises_when_not_loaded():
    """Если модель не загружена — RuntimeError."""
    from voice_assistant.speech.providers.vosk_tts import VoskTTSProvider, _state

    provider = VoskTTSProvider()
    original = _state._synth
    _state._synth = None
    _state._load_attempted = True
    try:
        import pytest

        with pytest.raises(RuntimeError, match="not loaded"):
            provider.synthesize("тест")
    finally:
        _state._synth = original
        _state._load_attempted = False


def test_vosk_tts_is_available_false_when_not_loaded():
    from voice_assistant.speech.providers.vosk_tts import VoskTTSProvider, _state

    provider = VoskTTSProvider()
    _state._synth = None
    _state._load_attempted = True
    try:
        assert provider.is_available() is False
    finally:
        _state._synth = None
        _state._load_attempted = False


def test_vosk_tts_active_providers(monkeypatch):
    """TTS_PROVIDER=vosk → vosk_tts в списке провайдеров первым."""
    import dataclasses

    import voice_assistant.speech.tts as tts_mod

    vosk_settings = dataclasses.replace(tts_mod.settings, tts_provider="vosk")
    monkeypatch.setattr(tts_mod, "settings", vosk_settings)
    providers = tts_mod._active_providers()
    assert providers[0].name == "vosk"
    assert len(providers) == 3
