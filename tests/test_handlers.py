from unittest.mock import MagicMock


def test_handlers_registry():
    from voice_assistant.nlu.handlers import _HANDLERS

    assert "weather" in _HANDLERS
    assert "time" in _HANDLERS
    assert "timer" in _HANDLERS
    assert "help" in _HANDLERS
    assert "youtube_search" in _HANDLERS
    assert "stop" in _HANDLERS
    assert "now_playing" in _HANDLERS


def test_stop_handler(mock_speak, mock_make_sound):
    from voice_assistant.nlu.handlers import StopHandler

    StopHandler().execute(None, listen=MagicMock())
    assert mock_speak.call_args[0][0] == "Хорошо."
    mock_make_sound.assert_called_once()


def test_now_playing_handler_no_video(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.services.browser as browser_mod
    from voice_assistant.nlu.handlers import NowPlayingHandler

    monkeypatch.setattr(browser_mod, "get_current_title", lambda: None)
    NowPlayingHandler().execute(None, listen=MagicMock())
    mock_speak.assert_called_with("Сейчас ничего не играет.")


def test_now_playing_handler_with_video(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.nlu.handlers as h_mod
    from voice_assistant.nlu.handlers import NowPlayingHandler

    monkeypatch.setattr(h_mod, "get_current_title", lambda: "Cool Video")
    NowPlayingHandler().execute(None, listen=MagicMock())
    assert mock_speak.call_args[0][0] == "Сейчас играет: Cool Video"


def test_execute_unknown_intent(mock_speak, mock_make_sound):
    from voice_assistant.nlu.handlers import execute_intent

    execute_intent("unknown_intent", None, listen=MagicMock())
    assert mock_speak.call_args[0][0] == "Я не знаю такую команду."


def test_weather_handler(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.nlu.handlers as h_mod
    from voice_assistant.nlu.handlers import WeatherHandler

    monkeypatch.setattr(h_mod, "get_weather_text", lambda city: "Погода: ясно")
    WeatherHandler().execute("Гомель", listen=MagicMock())
    assert mock_speak.call_args[0][0] == "Погода: ясно"
    mock_make_sound.assert_called_once()
