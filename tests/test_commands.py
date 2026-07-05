from voice_assistant.services.commands import (
    _format_timer_display,
    _handle_timer,
    _parse_timer_seconds,
    _plural,
    drain_speech_queue,
)


def test_parse_seconds_minutes():
    assert _parse_timer_seconds("5 минут") == 300


def test_parse_seconds_seconds():
    assert _parse_timer_seconds("30 секунд") == 30


def test_parse_seconds_hours():
    assert _parse_timer_seconds("2 часа") == 7200


def test_parse_seconds_default_minutes():
    assert _parse_timer_seconds("5") == 300


def test_parse_seconds_no_number():
    assert _parse_timer_seconds("минут") is None


def test_format_seconds():
    assert "5 секунд" in _format_timer_display(5)


def test_format_minutes():
    assert "5 минут" in _format_timer_display(300)


def test_format_hours():
    display = _format_timer_display(7200)
    assert "2 часа" in display


def test_format_complex():
    display = _format_timer_display(3661)
    assert "1 час" in display
    assert "1 минута" in display
    assert "1 секунда" in display


def test_plural_one():
    assert _plural(1, ("час", "часа", "часов")) == "час"


def test_plural_few():
    assert _plural(2, ("час", "часа", "часов")) == "часа"


def test_plural_many():
    assert _plural(5, ("час", "часа", "часов")) == "часов"


def test_plural_teens():
    assert _plural(11, ("час", "часа", "часов")) == "часов"


def test_handle_timer_no_payload(mock_speak):
    _handle_timer(None)
    mock_speak.assert_called_with("Укажите время для таймера. Например: таймер пять минут.")


def test_handle_timer_unparseable(mock_speak):
    _handle_timer("abc")
    mock_speak.assert_called_with("Не расслышала время. Повторите, например: таймер пять минут.")


def test_handle_timer_valid(mock_speak):
    _handle_timer("1 секунда")
    # First call announces the timer
    assert mock_speak.call_count == 1
    assert "Ставлю таймер" in mock_speak.call_args[0][0]


def test_drain_empty():
    drain_speech_queue()
