from unittest.mock import MagicMock


def test_browser_open_url(monkeypatch):
    import voice_assistant.services.browser as browser_mod

    mock_open = MagicMock()
    monkeypatch.setattr(browser_mod.webbrowser, "open", mock_open)
    browser_mod.open_browser_url("https://example.com")
    mock_open.assert_called_with("https://example.com")
    assert browser_mod._state._current_url == "https://example.com"


def test_browser_open_url_error(monkeypatch):
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod.webbrowser, "open", MagicMock(side_effect=Exception("fail")))
    browser_mod.open_browser_url("https://example.com")


def test_get_current_title_no_video():
    import voice_assistant.services.browser as browser_mod

    browser_mod._state._current_url = None
    assert browser_mod.get_current_title() is None


def test_get_current_title_with_url(monkeypatch):
    import voice_assistant.services.browser as browser_mod

    browser_mod._state._current_url = "https://youtube.com/watch?v=123"

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, url, download=False):
            return {"title": "Cool Video [Official]"}

    monkeypatch.setattr(browser_mod, "YoutubeDL", lambda opts: FakeYDL())
    title = browser_mod.get_current_title()
    assert title is not None
    assert "Cool Video" in title
    assert "[" not in title


def test_get_current_title_error(monkeypatch):
    import voice_assistant.services.browser as browser_mod

    browser_mod._state._current_url = "https://youtube.com/watch?v=123"

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, url, download=False):
            raise RuntimeError("network error")

    monkeypatch.setattr(browser_mod, "YoutubeDL", lambda opts: FakeYDL())
    assert browser_mod.get_current_title() is None


def test_get_current_title_empty_title(monkeypatch):
    import voice_assistant.services.browser as browser_mod

    browser_mod._state._current_url = "https://youtube.com/watch?v=123"

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, url, download=False):
            return {"title": ""}

    monkeypatch.setattr(browser_mod, "YoutubeDL", lambda opts: FakeYDL())
    assert browser_mod.get_current_title() is None


def test_clean_title():
    from voice_assistant.services.browser import _clean_title

    assert _clean_title("Hello [Official]") == "Hello"
    assert _clean_title("Song (feat. X)") == "Song"
    assert _clean_title("Emoji 🎵 Test") == "Emoji Test"
