from unittest.mock import MagicMock


class FakeSettings:
    """Fake settings for weather tests."""

    def __init__(self, default_city="Костюковка"):
        self.weather_default_city = default_city


# ── Open-Meteo tests ────────────────────────────────────────────────────


def test_open_meteo_success(monkeypatch):
    """Open-Meteo returns formatted weather text."""
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())

    mock_response_geo = MagicMock()
    mock_response_geo.json.return_value = {
        "results": [
            {"name": "Костюковка", "country": "Belarus", "latitude": 52.4, "longitude": 30.9}
        ]
    }
    mock_response_geo.raise_for_status = MagicMock()

    mock_response_weather = MagicMock()
    mock_response_weather.json.return_value = {
        "current": {
            "temperature_2m": 15.3,
            "apparent_temperature": 13.0,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 5.2,
            "weather_code": 3,
        }
    }
    mock_response_weather.raise_for_status = MagicMock()

    monkeypatch.setattr(
        weather_mod.requests,
        "get",
        MagicMock(side_effect=[mock_response_geo, mock_response_weather]),
    )

    result = weather_mod.get_weather_text("Костюковка")
    assert "15" in result
    assert "пасмурно" in result
    assert "13" in result
    assert "70" in result
    assert "5" in result


def test_open_meteo_city_not_found(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())

    mock_response = MagicMock()
    mock_response.json.return_value = {"results": None}
    mock_response.raise_for_status = MagicMock()

    monkeypatch.setattr(weather_mod.requests, "get", MagicMock(return_value=mock_response))

    assert "Не удалось определить город" in weather_mod.get_weather_text("nonexistent")


def test_open_meteo_network_error(monkeypatch):
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())
    monkeypatch.setattr(weather_mod.requests, "get", MagicMock(side_effect=Exception("fail")))

    assert "Не удалось получить прогноз" in weather_mod.get_weather_text("Костюковка")


def test_open_meteo_format_missing_data():
    from voice_assistant.services.weather import _format_open_meteo_weather

    result = _format_open_meteo_weather({}, "Костюковка")
    assert "Не удалось обработать" in result


# ── WMO code mapping ────────────────────────────────────────────────────


def test_wmo_code_clear():
    from voice_assistant.services.weather import _wmo_description

    assert _wmo_description(0) == "ясно"


def test_wmo_code_overcast():
    from voice_assistant.services.weather import _wmo_description

    assert _wmo_description(3) == "пасмурно"


def test_wmo_code_rain():
    from voice_assistant.services.weather import _wmo_description

    assert _wmo_description(61) == "небольшой дождь"


def test_wmo_code_thunderstorm():
    from voice_assistant.services.weather import _wmo_description

    assert _wmo_description(95) == "гроза"


def test_wmo_code_unknown():
    from voice_assistant.services.weather import _wmo_description

    assert _wmo_description(999) == "без уточнения"


# ── Default city fallback ────────────────────────────────────────────────


def test_default_city_used_when_no_arg(monkeypatch):
    """Без аргумента используется город из настроек."""
    import voice_assistant.services.weather as weather_mod

    monkeypatch.setattr(weather_mod, "settings", FakeSettings())

    mock_response_geo = MagicMock()
    mock_response_geo.json.return_value = {
        "results": [
            {"name": "Костюковка", "country": "Belarus", "latitude": 52.4, "longitude": 30.9}
        ]
    }
    mock_response_geo.raise_for_status = MagicMock()

    mock_response_weather = MagicMock()
    mock_response_weather.json.return_value = {
        "current": {
            "temperature_2m": 10.0,
            "apparent_temperature": 8.0,
            "relative_humidity_2m": 50,
            "wind_speed_10m": 3.0,
            "weather_code": 0,
        }
    }
    mock_response_weather.raise_for_status = MagicMock()

    monkeypatch.setattr(
        weather_mod.requests,
        "get",
        MagicMock(side_effect=[mock_response_geo, mock_response_weather]),
    )

    result = weather_mod.get_weather_text()
    assert "10" in result
    assert "ясно" in result
    assert "Костюковка" in result
