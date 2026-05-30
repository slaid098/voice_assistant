from src.weather import _format_weather


def test_format_weather():
    mock_data = {
        "current_condition": [
            {
                "temp_C": "15",
                "lang_ru": [{"value": "ясно"}],
                "windspeedKmph": "10",
                "humidity": "50",
            }
        ],
        "weather": [
            {
                "maxtempC": "20",
                "mintempC": "10",
            }
        ]
    }
    res = _format_weather(mock_data, "Москва")
    assert "Сейчас в Москва 15 градусов, ясно" in res
    assert "Сегодня от 10 до 20 градусов" in res
