from unittest.mock import MagicMock


def test_handle_timer_speaks_and_starts(monkeypatch, mock_speak):
    import voice_assistant.services.commands as cmd_mod

    timer_mock = MagicMock()
    monkeypatch.setattr(cmd_mod.threading, "Timer", timer_mock)

    cmd_mod._handle_timer("5 минут")

    assert mock_speak.call_count == 1
    assert "Ставлю таймер" in mock_speak.call_args[0][0]
    assert timer_mock.called
    assert timer_mock.return_value.daemon is True
    timer_mock.return_value.start.assert_called_once()


def test_handle_simple_command_time(mock_speak):
    from voice_assistant.services.commands import handle_simple_command

    handle_simple_command("time", None)
    assert mock_speak.call_count == 1
    assert "Сегодня" in mock_speak.call_args[0][0]


def test_handle_simple_command_help(mock_speak):
    from voice_assistant.services.commands import handle_simple_command

    handle_simple_command("help", None)
    assert mock_speak.call_count == 1
    assert "Вот что я умею" in mock_speak.call_args[0][0]


def test_handle_simple_command_timer(mock_speak, monkeypatch):
    import voice_assistant.services.commands as cmd_mod

    timer_mock = MagicMock()
    monkeypatch.setattr(cmd_mod.threading, "Timer", timer_mock)
    cmd_mod.handle_simple_command("timer", "5 минут")
    assert timer_mock.called


def test_get_time_text_format():
    from voice_assistant.services.commands import _get_time_text

    text = _get_time_text()
    assert "Сегодня" in text
    assert "текущее время" in text
    assert "." in text
    assert ":" in text
