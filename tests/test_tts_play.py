from unittest.mock import MagicMock


def test_play_bytes_wav(monkeypatch):
    """_play_bytes writes WAV to temp file and plays it."""
    import voice_assistant.speech.tts as tts_mod

    wav_header = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
        b"\x01\x00\x01\x00\x80\xbb\x00\x00\x00\x00\x00\x00"
        b"\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    mock_play = MagicMock()
    monkeypatch.setattr(tts_mod, "_play_file", mock_play)
    tts_mod._play_bytes(wav_header)
    mock_play.assert_called_once()
    args, _ = mock_play.call_args
    assert args[0].endswith(".wav")


def test_play_bytes_mp3(monkeypatch):
    """_play_bytes writes MP3 to temp file and plays it."""
    import voice_assistant.speech.tts as tts_mod

    mp3_data = b"ID3\x04\x00\x00\x00\x00\x00\x00fake mp3"
    mock_play = MagicMock()
    monkeypatch.setattr(tts_mod, "_play_file", mock_play)
    tts_mod._play_bytes(mp3_data)
    mock_play.assert_called_once()
    args, _ = mock_play.call_args
    assert args[0].endswith(".mp3")


def test_temp_audio_path_creates_and_deletes():
    """_temp_audio_path creates temp file and cleans up."""
    import os

    from voice_assistant.speech.tts import _temp_audio_path

    data = b"test audio data"
    with _temp_audio_path(data, ".wav") as path:
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == data
    assert not os.path.exists(path)


def test_play_file_exception_handled(monkeypatch):
    """_play_file catches exceptions without crashing."""
    import voice_assistant.speech.tts as tts_mod

    class PlayError(Exception):
        pass

    def raise_ex(path):
        raise PlayError("play error")

    monkeypatch.setattr(tts_mod.pygame.mixer, "Sound", raise_ex)
    monkeypatch.setattr(tts_mod.pygame.mixer, "get_busy", lambda: False)
    tts_mod._play_file("/fake/path.mp3")
