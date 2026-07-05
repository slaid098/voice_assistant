from voice_assistant.nlu.intent import parse_voice_intent


def test_youtube_search():
    r = parse_voice_intent("ютуб котики")
    assert r is not None
    assert r["intent"] == "youtube_search"
    assert r["payload"] == "котики"


def test_youtube_search_with_find():
    r = parse_voice_intent("найди на ютубе музыку")
    assert r is not None
    assert r["intent"] == "youtube_search"


def test_weather():
    r = parse_voice_intent("погода москва")
    assert r is not None
    assert r["intent"] == "weather"
    assert "москва" in r["payload"]


def test_time():
    r = parse_voice_intent("время")
    assert r is not None
    assert r["intent"] == "time"


def test_timer():
    r = parse_voice_intent("таймер пять минут")
    assert r is not None
    assert r["intent"] == "timer"
    assert "пять" in r["payload"]
    assert "минут" in r["payload"]


def test_stop():
    r = parse_voice_intent("стоп")
    assert r is not None
    assert r["intent"] == "stop"


def test_help():
    r = parse_voice_intent("помощь")
    assert r is not None
    assert r["intent"] == "help"


def test_now_playing_nazvanie():
    r = parse_voice_intent("название")
    assert r is not None
    assert r["intent"] == "now_playing"


def test_now_playing_chto_igraet():
    r = parse_voice_intent("что играет")
    assert r is not None
    assert r["intent"] == "now_playing"


def test_unknown_command():
    assert parse_voice_intent("какая то бессмыслица") is None


def test_empty():
    assert parse_voice_intent("") is None


def test_none():
    assert parse_voice_intent(None) is None


def test_normalize_youtube_latin():
    r = parse_voice_intent("youtube cats")
    assert r is not None
    assert r["intent"] == "youtube_search"


def test_normalize_youtube_you_tube():
    r = parse_voice_intent("you tube music")
    assert r is not None
    assert r["intent"] == "youtube_search"


def test_normalize_yutub():
    r = parse_voice_intent("ютюб видео")
    assert r is not None
    assert r["intent"] == "youtube_search"
