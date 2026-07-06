def test_search_youtube_success(monkeypatch):
    import voice_assistant.services.youtube as yt_mod

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, query, download=False):
            return {
                "entries": [
                    {"title": "Cool Video", "url": "https://youtube.com/watch?v=1"},
                    {"title": "Another [Official]", "webpage_url": "https://youtube.com/watch?v=2"},
                    {"title": "Third", "id": "abc123"},
                ]
            }

    monkeypatch.setattr(yt_mod, "YoutubeDL", lambda opts: FakeYDL())
    result = yt_mod.search_youtube_videos("test")
    assert len(result) == 3
    assert result[0]["title"] == "Cool Video"
    assert result[0]["url"] == "https://youtube.com/watch?v=1"
    assert result[1]["title"] == "Another"
    assert result[2]["url"] == "https://www.youtube.com/watch?v=abc123"


def test_search_youtube_empty(monkeypatch):
    import voice_assistant.services.youtube as yt_mod

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, query, download=False):
            return {"entries": []}

    monkeypatch.setattr(yt_mod, "YoutubeDL", lambda opts: FakeYDL())
    assert yt_mod.search_youtube_videos("nothing") == []


def test_search_youtube_no_entries(monkeypatch):
    import voice_assistant.services.youtube as yt_mod

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, query, download=False):
            return {}

    monkeypatch.setattr(yt_mod, "YoutubeDL", lambda opts: FakeYDL())
    assert yt_mod.search_youtube_videos("test") == []


def test_search_youtube_exception(monkeypatch):
    import voice_assistant.services.youtube as yt_mod

    class FakeYDL:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def extract_info(self, query, download=False):
            raise RuntimeError("network error")

    monkeypatch.setattr(yt_mod, "YoutubeDL", lambda opts: FakeYDL())
    assert yt_mod.search_youtube_videos("test") == []


def test_clean_title():
    from voice_assistant.speech.text_normalize import clean_title

    assert clean_title("Hello [Official]") == "Hello"
    assert clean_title("Song (feat. X)") == "Song"
    assert clean_title("Emoji 🎵 Test") == "Emoji Test"
    assert clean_title("  spaces  ") == "spaces"


def test_format_entry():
    from voice_assistant.services.youtube import _format_entry

    entry = {"title": "Test [Video]", "url": "https://example.com"}
    result = _format_entry(entry)
    assert result["title"] == "Test"
    assert result["url"] == "https://example.com"
