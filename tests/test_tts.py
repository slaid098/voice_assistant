from unittest.mock import MagicMock


def test_speak_calls_gtts_and_plays(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    class FakeTTS:
        def __init__(self, text, **kw):
            self.text = text

        def write_to_fp(self, fp):
            fp.write(b"fake mp3 data")

    monkeypatch.setattr(tts_mod.gtts, "gTTS", FakeTTS)

    sound_mock = MagicMock()
    monkeypatch.setattr(tts_mod.pygame.mixer, "Sound", lambda path: sound_mock)
    monkeypatch.setattr(tts_mod.pygame.mixer, "get_busy", MagicMock(side_effect=[True, False]))
    monkeypatch.setattr(tts_mod.pygame.time, "wait", MagicMock())
    monkeypatch.setattr(tts_mod, "_ensure_mixer", MagicMock())

    tts_mod.speak("привет")

    sound_mock.play.assert_called_once()


def test_speak_exception_handled(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    def raise_ex(text, **kw):
        raise RuntimeError("network error")

    monkeypatch.setattr(tts_mod.gtts, "gTTS", raise_ex)
    monkeypatch.setattr(tts_mod, "_ensure_mixer", MagicMock())

    tts_mod.speak("привет")


def test_ensure_mixer_already_initialized(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    monkeypatch.setattr(tts_mod.pygame.mixer, "get_init", lambda: (24000, -16, 1))
    tts_mod._ensure_mixer()


def test_play_file_exception_handled(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    def raise_ex(path):
        raise RuntimeError("play error")

    monkeypatch.setattr(tts_mod.pygame.mixer, "Sound", raise_ex)
    monkeypatch.setattr(tts_mod.pygame.mixer, "get_busy", lambda: False)
    tts_mod._play_file("/fake/path.mp3")


def test_temp_mp3_path_context():
    import io

    from voice_assistant.speech.tts import _temp_mp3_path

    data = io.BytesIO(b"fake mp3")
    with _temp_mp3_path(data) as path:
        assert isinstance(path, str)
    # After context, file is deleted
