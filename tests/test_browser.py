import dataclasses
import os
from unittest.mock import MagicMock


def test_open_url_windows_app_mode(monkeypatch):
    """На Windows URL открывается через vivaldi --app=<url>."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    test_settings = dataclasses.replace(browser_mod.settings, browser_path="")
    monkeypatch.setattr(browser_mod, "settings", test_settings)
    monkeypatch.setattr(browser_mod, "_detect_vivaldi_path", lambda: "C:\\Vivaldi\\vivaldi.exe")
    mock_popen = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "Popen", mock_popen)
    mock_run = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "run", mock_run)

    state.open_url("https://youtube.com/watch?v=1")

    mock_popen.assert_called_once_with(
        ["C:\\Vivaldi\\vivaldi.exe", "--app=https://youtube.com/watch?v=1"],
        stdout=browser_mod.subprocess.DEVNULL,
        stderr=browser_mod.subprocess.DEVNULL,
    )
    mock_run.assert_not_called()
    assert state._has_open_window is True


def test_open_url_windows_taskkill_before_new(monkeypatch):
    """Перед новым открытием вызывается taskkill /IM vivaldi.exe."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    test_settings = dataclasses.replace(browser_mod.settings, browser_path="")
    monkeypatch.setattr(browser_mod, "settings", test_settings)
    monkeypatch.setattr(browser_mod, "_detect_vivaldi_path", lambda: "C:\\Vivaldi\\vivaldi.exe")
    mock_popen = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "Popen", mock_popen)
    mock_run = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "run", mock_run)

    state.open_url("https://youtube.com/watch?v=1")
    state.open_url("https://youtube.com/watch?v=2")

    assert mock_popen.call_count == 2
    assert mock_run.call_count == 1
    mock_run.assert_called_once_with(
        ["taskkill", "/IM", "vivaldi.exe"],
        capture_output=True,
        check=False,
    )


def test_open_url_vivaldi_not_found(monkeypatch):
    """Vivaldi не найден — лог error, не падает, окно не открыто."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    test_settings = dataclasses.replace(browser_mod.settings, browser_path="")
    monkeypatch.setattr(browser_mod, "settings", test_settings)
    monkeypatch.setattr(browser_mod, "_detect_vivaldi_path", lambda: None)
    mock_popen = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "Popen", mock_popen)

    state.open_url("https://example.com")

    mock_popen.assert_not_called()
    assert state._has_open_window is False


def test_browser_path_from_settings(monkeypatch):
    """BROWSER_PATH задан в settings — используется он, авто-detect не вызывается."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    test_settings = dataclasses.replace(browser_mod.settings, browser_path="/custom/vivaldi.exe")
    monkeypatch.setattr(browser_mod, "settings", test_settings)

    detect_called = {"yes": False}

    def _fail_if_called() -> str | None:
        detect_called["yes"] = True
        raise AssertionError("auto-detect должен не вызываться при заданном BROWSER_PATH")

    monkeypatch.setattr(browser_mod, "_detect_vivaldi_path", _fail_if_called)
    mock_popen = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "Popen", mock_popen)
    mock_run = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "run", mock_run)

    state.open_url("https://youtube.com/watch?v=1")

    mock_popen.assert_called_once_with(
        ["/custom/vivaldi.exe", "--app=https://youtube.com/watch?v=1"],
        stdout=browser_mod.subprocess.DEVNULL,
        stderr=browser_mod.subprocess.DEVNULL,
    )
    mock_run.assert_not_called()
    assert state._has_open_window is True
    assert detect_called["yes"] is False


def test_open_url_non_windows_fallback_webbrowser(monkeypatch):
    """На не-Windows — fallback на webbrowser.open."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", False)
    mock_open = MagicMock()
    monkeypatch.setattr(browser_mod.webbrowser, "open", mock_open)
    mock_popen = MagicMock()
    monkeypatch.setattr(browser_mod.subprocess, "Popen", mock_popen)

    state.open_url("https://example.com")

    mock_open.assert_called_once_with("https://example.com")
    mock_popen.assert_not_called()


def test_open_url_non_windows_webbrowser_error(monkeypatch):
    """На не-Windows webbrowser падает — лог error, не падает."""
    import webbrowser

    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", False)
    monkeypatch.setattr(
        browser_mod.webbrowser,
        "open",
        MagicMock(side_effect=webbrowser.Error("fail")),
    )

    state.open_url("https://example.com")


def test_open_url_non_windows_oserror_fallback(monkeypatch):
    """На не-Windows OSError тоже ловится (часть narrowed except)."""
    import voice_assistant.services.browser as browser_mod

    state = browser_mod.BrowserState()
    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", False)
    monkeypatch.setattr(
        browser_mod.webbrowser,
        "open",
        MagicMock(side_effect=OSError("fail")),
    )

    state.open_url("https://example.com")


def test_detect_vivaldi_path_local_appdata(monkeypatch):
    """Авто-detect находит Vivaldi в LOCALAPPDATA."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("LOCALAPPDATA", "C:\\Users\\test\\AppData\\Local")
    expected = os.path.join(
        "C:\\Users\\test\\AppData\\Local", "Vivaldi", "Application", "vivaldi.exe"
    )
    monkeypatch.setattr(browser_mod.os.path, "isfile", lambda p: p == expected)

    path = browser_mod._detect_vivaldi_path()
    assert path is not None
    assert path.endswith("vivaldi.exe")


def test_detect_vivaldi_path_not_found(monkeypatch):
    """Авто-detect возвращает None, если Vivaldi нигде не найден."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("LOCALAPPDATA", "C:\\nonexistent")
    monkeypatch.setattr(browser_mod.os.path, "isfile", lambda p: False)

    path = browser_mod._detect_vivaldi_path()
    assert path is None


def test_detect_vivaldi_path_non_windows(monkeypatch):
    """На не-Windows авто-detect всегда возвращает None."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "_IS_WINDOWS", False)
    path = browser_mod._detect_vivaldi_path()
    assert path is None


def test_get_current_title_no_window(monkeypatch):
    """На non-Windows или нет окна — None."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "get_youtube_window_title", lambda: None)
    assert browser_mod.get_current_title() is None


def test_get_current_title_from_window(monkeypatch):
    """Заголовок окна даёт название видео (ловит autoplay)."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(browser_mod, "get_youtube_window_title", lambda: "New Video After Autoplay")
    assert browser_mod.get_current_title() == "New Video After Autoplay"


def test_get_current_title_strips_youtube_suffix(monkeypatch):
    """Заголовок 'Song - YouTube - Vivaldi' → 'Song'."""
    import voice_assistant.services.browser as browser_mod

    monkeypatch.setattr(
        browser_mod,
        "get_youtube_window_title",
        lambda: "Cool Song - YouTube - Vivaldi",
    )
    assert browser_mod.get_current_title() == "Cool Song"


def test_clean_title():
    from voice_assistant.speech.text_normalize import clean_title

    assert clean_title("Hello [Official]") == "Hello"
    assert clean_title("Song (feat. X)") == "Song"
    assert clean_title("Emoji 🎵 Test") == "Emoji Test"
    assert clean_title("  spaces  ") == "spaces"


def test_get_youtube_window_title_non_windows():
    """На non-Windows win32gui недоступен → None."""
    import sys

    import voice_assistant.services.browser as browser_mod

    if sys.platform != "win32":
        assert browser_mod.get_youtube_window_title() is None
