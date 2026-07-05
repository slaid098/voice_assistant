from unittest.mock import MagicMock


def test_youtube_flow_no_query_listen_returns_none(mock_speak, mock_make_sound):
    from voice_assistant.services.youtube_flow import run_youtube_flow

    listen = MagicMock(return_value=None)
    run_youtube_flow(None, listen=listen)
    listen.assert_called_once()


def test_youtube_flow_no_results(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.services.youtube_flow as yf_mod
    from voice_assistant.services.youtube_flow import run_youtube_flow

    listen = MagicMock(return_value="котики")
    monkeypatch.setattr(yf_mod, "search_youtube_videos", lambda q: [])
    run_youtube_flow(None, listen=listen)
    mock_speak.assert_any_call("Ничего не найдено.")


def test_youtube_flow_play_first(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.services.youtube_flow as yf_mod
    from voice_assistant.services.youtube_flow import run_youtube_flow

    videos = [{"title": "Cool", "url": "https://youtube.com/watch?v=1"}]
    monkeypatch.setattr(yf_mod, "search_youtube_videos", lambda q: videos)
    monkeypatch.setattr(yf_mod, "open_browser_url", MagicMock())

    listen = MagicMock(side_effect=["котики", "включить"])
    run_youtube_flow(None, listen=listen)
    mock_speak.assert_any_call("Включаю.")
    mock_speak.assert_any_call("Сделано.")


def test_youtube_flow_stop(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.services.youtube_flow as yf_mod
    from voice_assistant.services.youtube_flow import run_youtube_flow

    videos = [{"title": "Cool", "url": "https://youtube.com/watch?v=1"}]
    monkeypatch.setattr(yf_mod, "search_youtube_videos", lambda q: videos)
    listen = MagicMock(side_effect=["котики", "стоп"])
    run_youtube_flow(None, listen=listen)
    mock_speak.assert_any_call("Поиск отменён.")


def test_youtube_flow_navigate_then_play(mock_speak, mock_make_sound, monkeypatch):
    import voice_assistant.services.youtube_flow as yf_mod
    from voice_assistant.services.youtube_flow import run_youtube_flow

    videos = [
        {"title": "First", "url": "https://youtube.com/watch?v=1"},
        {"title": "Second", "url": "https://youtube.com/watch?v=2"},
    ]
    monkeypatch.setattr(yf_mod, "search_youtube_videos", lambda q: videos)
    monkeypatch.setattr(yf_mod, "open_browser_url", MagicMock())

    listen = MagicMock(side_effect=["котики", "дальше", "включить"])
    run_youtube_flow(None, listen=listen)
    mock_speak.assert_any_call("Включаю.")
