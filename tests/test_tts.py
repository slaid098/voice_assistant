from unittest.mock import MagicMock


def test_speak_uses_google_when_available(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = MagicMock()
    mock_google.is_available.return_value = True
    mock_google.synthesize.return_value = b"ID3\x04\x00fake mp3"
    monkeypatch.setattr(tts_mod, "_providers", [mock_google])

    mock_play = MagicMock()
    monkeypatch.setattr(tts_mod, "_play_bytes", mock_play)

    tts_mod.speak("привет")

    mock_google.synthesize.assert_called_with("привет")
    mock_play.assert_called_once()


def test_speak_fallback_to_piper(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = MagicMock()
    mock_google.is_available.return_value = False

    mock_piper = MagicMock()
    mock_piper.is_available.return_value = True
    mock_piper.synthesize.return_value = b"RIFF\x00\x00\x00\x00fake wav"

    monkeypatch.setattr(tts_mod, "_providers", [mock_google, mock_piper])
    monkeypatch.setattr(tts_mod, "_play_bytes", MagicMock())

    tts_mod.speak("привет")

    mock_google.synthesize.assert_not_called()
    mock_piper.synthesize.assert_called_with("привет")


def test_speak_fallback_on_exception(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = MagicMock()
    mock_google.is_available.return_value = True
    mock_google.synthesize.side_effect = Exception("network error")

    mock_piper = MagicMock()
    mock_piper.is_available.return_value = True
    mock_piper.synthesize.return_value = b"RIFF fake wav"

    monkeypatch.setattr(tts_mod, "_providers", [mock_google, mock_piper])
    monkeypatch.setattr(tts_mod, "_play_bytes", MagicMock())

    tts_mod.speak("привет")

    mock_google.synthesize.assert_called_once()
    mock_piper.synthesize.assert_called_once()


def test_speak_all_fail_makes_error_sound(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = MagicMock()
    mock_google.is_available.return_value = False

    mock_piper = MagicMock()
    mock_piper.is_available.return_value = False

    mock_callback = MagicMock()
    monkeypatch.setattr(tts_mod, "_providers", [mock_google, mock_piper])

    tts_mod.speak("привет", on_all_fail=mock_callback)

    mock_callback.assert_called_once()


def test_is_mp3():
    from voice_assistant.speech.tts import _is_mp3

    assert _is_mp3(b"ID3\x04\x00") is True
    assert _is_mp3(b"\xff\xfb\x00") is True
    assert _is_mp3(b"\xff\xf3\x00") is True
    assert _is_mp3(b"RIFF\x00\x00") is False
    assert _is_mp3(b"") is False


def test_google_tts_synthesize(monkeypatch):
    from voice_assistant.speech.providers.google_tts import GoogleTTSProvider

    class FakeTTS:
        def __init__(self, text, **kw):
            self.text = text

        def write_to_fp(self, fp):
            fp.write(b"ID3fake mp3 data")

    monkeypatch.setattr("gtts.gTTS", FakeTTS)
    provider = GoogleTTSProvider()
    result = provider.synthesize("привет")
    assert b"ID3" in result


def test_google_tts_is_available(monkeypatch):
    import socket

    from voice_assistant.speech.providers.google_tts import GoogleTTSProvider

    monkeypatch.setattr(socket, "gethostbyname", lambda host: "1.2.3.4")
    provider = GoogleTTSProvider()
    assert provider.is_available() is True


def test_google_tts_not_available(monkeypatch):
    import socket

    from voice_assistant.speech.providers.google_tts import GoogleTTSProvider

    def raise_dns(host):
        raise socket.gaierror("DNS failed")

    monkeypatch.setattr(socket, "gethostbyname", raise_dns)
    provider = GoogleTTSProvider()
    assert provider.is_available() is False
