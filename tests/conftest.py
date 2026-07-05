import os
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _no_env() -> Generator[None, None, None]:
    """Isolate env vars per test."""
    saved = dict(os.environ)
    os.environ.pop("WAKE_WORD", None)
    os.environ.pop("WAKE_THRESHOLD", None)
    os.environ.pop("OPENWEATHER_API_KEY", None)
    os.environ.pop("WEATHER_DEFAULT_CITY", None)
    os.environ.pop("YOUTUBE_SEARCH_LIMIT", None)
    yield
    os.environ.clear()
    os.environ.update(saved)


@pytest.fixture(autouse=True)
def _dummy_audio(monkeypatch) -> None:
    """Avoid real audio device in tests."""
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


@pytest.fixture
def mock_speak(monkeypatch) -> MagicMock:
    """Mock TTS speak to avoid audio device."""
    import voice_assistant.audio.sounds as sounds_mod
    import voice_assistant.nlu.handlers as h_mod
    import voice_assistant.services.commands as cmd_mod
    import voice_assistant.services.youtube_flow as yf_mod
    import voice_assistant.speech.tts as tts_mod

    mock = MagicMock()
    monkeypatch.setattr(tts_mod, "speak", mock)
    monkeypatch.setattr(cmd_mod, "speak", mock)
    monkeypatch.setattr(h_mod, "speak", mock)
    monkeypatch.setattr(yf_mod, "speak", mock)
    monkeypatch.setattr(sounds_mod, "speak", mock)
    return mock


@pytest.fixture
def mock_make_sound(monkeypatch) -> MagicMock:
    """Mock make_sound to avoid audio device."""
    import voice_assistant.assistant as a_mod
    import voice_assistant.audio.sounds as sounds_mod
    import voice_assistant.nlu.handlers as h_mod
    import voice_assistant.services.youtube_flow as yf_mod

    mock = MagicMock()
    monkeypatch.setattr(sounds_mod, "make_sound", mock)
    monkeypatch.setattr(a_mod, "make_sound", mock)
    monkeypatch.setattr(h_mod, "make_sound", mock)
    monkeypatch.setattr(yf_mod, "make_sound", mock)
    return mock
