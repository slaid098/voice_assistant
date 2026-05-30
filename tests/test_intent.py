from src.intent import parse_voice_intent, _strip_wake_word


def test_strip_wake_word():
    assert _strip_wake_word("привет вики погода") == "погода"
    assert _strip_wake_word("окей вики найди песню") == "найди песню"
    assert _strip_wake_word("слушай вики погода в москве") == "погода в москве"


def test_parse_voice_intent_weather():
    res = parse_voice_intent("вики какая погода в париже")
    assert res is not None
    assert res["intent"] == "weather"
    assert res["payload"] == "в париже"


def test_parse_voice_intent_youtube():
    res = parse_voice_intent("вики найди на ютубе старые песни")
    assert res is not None
    assert res["intent"] == "youtube_search"
    assert res["payload"] == "старые песни"
