from voice_assistant.services.youtube_flow import (
    _build_video_prompt,
    _get_next_index,
    _parse_pagination_response,
)


def test_parse_play():
    assert _parse_pagination_response("включить") == "play"


def test_parse_play_davay():
    assert _parse_pagination_response("давай это") == "play"


def test_parse_next():
    assert _parse_pagination_response("дальше") == "next"


def test_parse_back():
    assert _parse_pagination_response("назад") == "back"


def test_parse_stop():
    assert _parse_pagination_response("стоп") == "stop"


def test_parse_unknown():
    assert _parse_pagination_response("абракадабра") == "unknown"


def test_get_next_index_next():
    assert _get_next_index(index=0, action="next", total=10) == 1


def test_get_next_index_next_at_end(mock_speak):
    assert _get_next_index(index=9, action="next", total=10) == 9


def test_get_next_index_back():
    assert _get_next_index(index=5, action="back", total=10) == 4


def test_get_next_index_back_at_start(mock_speak):
    assert _get_next_index(index=0, action="back", total=10) == 0


def test_get_next_index_unknown():
    assert _get_next_index(index=0, action="unknown", total=10) is None


def test_build_video_prompt_first(mock_speak):
    prompt = _build_video_prompt(query="музыка", title="Cool Song", index=0)
    assert "Вот что я нашла по запросу музыка" in prompt
    assert "Cool Song" in prompt


def test_build_video_prompt_subsequent(mock_speak):
    prompt = _build_video_prompt(query="музыка", title="Cool Song", index=2)
    assert "Видео номер" in prompt
    assert "Cool Song" in prompt
    assert "Вот что я нашла" not in prompt
