from unittest.mock import MagicMock, call


def test_crash_handler_makes_sound_and_speaks(monkeypatch, mock_speak, mock_make_sound):
    """_crash_handler plays error sound and speaks error message."""
    import voice_assistant.cli as cli_mod

    cli_mod._crash_handler(RuntimeError, RuntimeError("test"), None)
    mock_make_sound.assert_called_once()
    assert mock_speak.call_count >= 1


def test_main_loop_handles_keyboard_interrupt(monkeypatch):
    """main() exits on KeyboardInterrupt."""
    import voice_assistant.cli as cli_mod

    call_count = [0]

    def fake_step():
        call_count[0] += 1
        if call_count[0] == 1:
            raise KeyboardInterrupt

    monkeypatch.setattr(cli_mod, "run_assistant_step", fake_step)
    monkeypatch.setattr(cli_mod, "setup_logging", MagicMock())
    monkeypatch.setattr(cli_mod, "init_sounds", MagicMock())
    mock_piper = MagicMock()
    monkeypatch.setattr(cli_mod, "preload_piper", mock_piper)
    mock_wake = MagicMock()
    monkeypatch.setattr(cli_mod, "preload_wake_word_detector", mock_wake)
    mock_sound = MagicMock()
    monkeypatch.setattr(cli_mod, "make_sound", mock_sound)
    cli_mod.main()  # should exit cleanly

    # preload_piper must be called with wait=True (blocking before STARTUP beep)
    mock_piper.assert_called_once_with(wait=True)
    mock_wake.assert_called_once()
    # STARTUP sound must play after both preloads
    mock_sound.assert_called_once()
    assert mock_sound.call_args == call(cli_mod.Sound.STARTUP)
