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


def test_get_current_title_no_window(monkeypatch):
    """On non-Windows or no YouTube window — returns None."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "get_youtube_window_title", lambda: None)
    assert browser_mod.get_current_title() is None


def test_get_current_title_from_window(monkeypatch):
    """Window title gives current video title (catches autoplay)."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "get_youtube_window_title", lambda: "New Video After Autoplay")
    # Title has no " - YouTube" suffix → returned as-is
    assert browser_mod.get_current_title() == "New Video After Autoplay"


def test_get_current_title_strips_youtube_suffix(monkeypatch):
    """Window title 'Song - YouTube - Google Chrome' → 'Song'."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(
        browser_mod,
        "get_youtube_window_title",
        lambda: "Cool Song - YouTube - Google Chrome",
    )
    assert browser_mod.get_current_title() == "Cool Song"


def test_clean_title():
    from voice_assistant.services.browser import _clean_title

    assert _clean_title("Hello [Official]") == "Hello"
    assert _clean_title("Song (feat. X)") == "Song"
    assert _clean_title("Emoji 🎵 Test") == "Emoji Test"
    assert _clean_title("  spaces  ") == "spaces"


def test_get_youtube_window_title_non_windows():
    """On non-Windows, returns None (win32gui not available)."""
    import sys

    import voice_assistant.services.browser as browser_mod

    if sys.platform != "win32":
        assert browser_mod.get_youtube_window_title() is None
