from unittest.mock import MagicMock


class FakeSettings:
    """Fake settings for weather tests."""

    def __init__(self, api_key="test123", default_city="Гомель"):
        self.openweather_api_key = api_key
        self.weather_default_city = default_city


def test_weather_no_api_key(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings(api_key=""))
    result = weather_mod.get_weather_text()
    assert "Не настроен ключ" in result


def test_weather_success(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())

    mock_response_geo = MagicMock()
    mock_response_geo.json.return_value = [
        {"lat": 52.4, "lon": 30.9, "name": "Gomel", "country": "BY"}
    ]
    mock_response_geo.raise_for_status = MagicMock()

    mock_response_weather = MagicMock()
    mock_response_weather.json.return_value = {
        "main": {"temp": 20.5, "feels_like": 19.0, "humidity": 60},
        "wind": {"speed": 3.5},
        "weather": [{"description": "ясно"}],
    }
    mock_response_weather.raise_for_status = MagicMock()

    monkeypatch.setattr(
        weather_mod.requests,
        "get",
        MagicMock(side_effect=[mock_response_geo, mock_response_weather]),
    )

    result = weather_mod.get_weather_text("Гомель")
    assert "20" in result
    assert "ясно" in result
    assert "60" in result


def test_weather_city_not_found(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())

    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()

    monkeypatch.setattr(weather_mod.requests, "get", MagicMock(return_value=mock_response))

    assert "Не удалось определить город" in weather_mod.get_weather_text("nonexistent")


def test_weather_network_error(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())
    monkeypatch.setattr(weather_mod.requests, "get", MagicMock(side_effect=Exception("fail")))

    assert "Не удалось получить прогноз" in weather_mod.get_weather_text("Гомель")


def test_format_weather_missing_data():
    from voice_assistant.services.weather import _format_weather

    result = _format_weather({}, "Гомель")
    assert "Не удалось обработать" in result
