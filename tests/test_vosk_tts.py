"""Тесты VoskTTSProvider."""

import pytest


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


class TestSanitizeForVosk:
    """Санитизация текста для Vosk TTS — защита от краха G2P."""

    def test_pure_cyrillic_unchanged(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        assert _sanitize_for_vosk("Привет, как дела?") == "Привет, как дела?"

    def test_chinese_characters_stripped(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Музыка 音乐 2026")
        assert "音乐" not in result
        assert "Музыка" in result

    def test_underscores_stripped(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Eminem_Lose_Yourself")
        assert "_" not in result

    def test_special_chars_stripped(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Тест @#$% символы")
        assert "@" not in result
        assert "#" not in result
        assert "Тест" in result
        assert "символы" in result

    def test_emoji_remnants_stripped(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Котики 😺 играют")
        assert "😺" not in result
        assert "Котики" in result
        assert "играют" in result

    def test_punctuation_preserved(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Привет! Как дела? Хорошо.")
        assert "!" in result
        assert "?" in result
        assert "." in result

    def test_spaces_collapsed(self):
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        result = _sanitize_for_vosk("Текст   с    пробелами")
        assert "  " not in result

    def test_youtube_title_with_mixed_scripts(self):
        """Реальный кейс: YouTube-заголовок с китайщиной и цифрами."""
        from voice_assistant.speech.providers.vosk_tts import _sanitize_for_vosk

        title = "Музыка 2026 音乐 [OFFICIAL] #trending"
        result = _sanitize_for_vosk(title)
        assert "音乐" not in result
        assert "#" not in result
        assert "[" not in result
        assert "Музыка" in result
