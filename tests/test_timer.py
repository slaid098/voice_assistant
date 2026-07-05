from unittest.mock import MagicMock


def test_handle_timer_replaces_previous(mock_speak, monkeypatch):
    """Setting a new timer cancels the previous one."""
    import voice_assistant.services.commands as cmd_mod

    old_timer = MagicMock()
    monkeypatch.setattr(cmd_mod._timer_state, "_active_timer", old_timer)

    new_timer = MagicMock()
    monkeypatch.setattr(cmd_mod.threading, "Timer", MagicMock(return_value=new_timer))

    cmd_mod._handle_timer("5 минут")
    old_timer.cancel.assert_called_once()
    new_timer.start.assert_called_once()


def test_timer_done_speaks_via_queue(mock_speak, monkeypatch):
    """Timer callback puts message in speech queue."""
    import time

    import voice_assistant.services.commands as cmd_mod

    monkeypatch.setattr(cmd_mod.threading, "Timer", cmd_mod.threading.Timer)
    cmd_mod._handle_timer("1 секунда")

    # Wait for timer to fire
    time.sleep(2)

    assert cmd_mod._speech_queue.qsize() >= 1
    msg = cmd_mod._speech_queue.get_nowait()
    assert "Таймер" in msg
    assert "истёк" in msg
