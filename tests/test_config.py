import pytest

from voice_assistant.config import Intent, IntentRule, _load_settings


def test_settings_defaults():
    s = _load_settings()
    assert s.wake_word == "вики"
    assert s.wake_threshold == 70
    assert s.wake_timeout_ms == 30000
    assert s.command_timeout_ms == 6000
    assert s.samplerate == 16000
    assert s.chunk_ms == 100
    assert s.vad_threshold == 200.0
    assert s.silence_limit_ms == 1800
    assert s.youtube_search_limit == 10
    assert s.weather_default_city == "Костюковка"
    assert s.openweather_api_key == ""
    assert s.tts_provider == "google"
    assert s.tts_cache_size == 50


def test_settings_tts_provider_from_env(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "piper")
    s = _load_settings()
    assert s.tts_provider == "piper"


def test_settings_silence_limit_from_env(monkeypatch):
    monkeypatch.setenv("SILENCE_LIMIT_MS", "1000")
    s = _load_settings()
    assert s.silence_limit_ms == 1000


def test_settings_tts_cache_size_from_env(monkeypatch):
    monkeypatch.setenv("TTS_CACHE_SIZE", "100")
    s = _load_settings()
    assert s.tts_cache_size == 100


def test_settings_wake_word_from_env(monkeypatch):
    monkeypatch.setenv("WAKE_WORD", "маркиза")
    s = _load_settings()
    assert s.wake_word == "маркиза"


def test_settings_openweather_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test123")
    s = _load_settings()
    assert s.openweather_api_key == "test123"


def test_settings_frozen():
    s = _load_settings()
    with pytest.raises((AttributeError, TypeError)):
        s.wake_word = "other"


def test_intent_enum_values():
    assert Intent.YOUTUBE_SEARCH.value == "youtube_search"
    assert Intent.WEATHER.value == "weather"
    assert Intent.NOW_PLAYING.value == "now_playing"
    assert Intent.STOP.value == "stop"


def test_intent_rules_count():
    s = _load_settings()
    assert len(s.intent_rules) == 7


def test_intent_rule_types():
    s = _load_settings()
    rule = s.intent_rules[0]
    assert isinstance(rule, IntentRule)
    assert rule.intent == Intent.YOUTUBE_SEARCH
    assert isinstance(rule.keywords, list)
    assert isinstance(rule.threshold, int)
    assert isinstance(rule.has_payload, bool)


def test_now_playing_rule():
    s = _load_settings()
    now_playing = [r for r in s.intent_rules if r.intent == Intent.NOW_PLAYING]
    assert len(now_playing) == 1
    assert "название" in now_playing[0].keywords


def test_wake_aliases():
    s = _load_settings()
    assert "вики" in s.wake_aliases
    assert "вика" in s.wake_aliases
