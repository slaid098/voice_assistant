from src.commands import _plural, _parse_timer_seconds, _format_timer_display


def test_plural_seconds():
    assert _plural(1, ("секунда", "секунды", "секунд")) == "секунда"
    assert _plural(2, ("секунда", "секунды", "секунд")) == "секунды"
    assert _plural(5, ("секунда", "секунды", "секунд")) == "секунд"


def test_parse_timer_seconds():
    assert _parse_timer_seconds("5 минут") == 300
    assert _parse_timer_seconds("10 секунд") == 10
    assert _parse_timer_seconds("1 час") == 3600


def test_format_timer_display():
    assert _format_timer_display(65) == "1 минута 5 секунд"
