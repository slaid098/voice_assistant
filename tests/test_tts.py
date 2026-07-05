from unittest.mock import MagicMock


def _make_mock_provider(*, is_cloud: bool, available: bool, audio: bytes = b"") -> MagicMock:
    provider = MagicMock()
    provider.name = "mock"
    provider.is_cloud = is_cloud
    provider.is_available.return_value = available
    provider.synthesize.return_value = audio
    provider.fixed_phrase.return_value = None
    return provider


def test_speak_uses_google_when_available(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=True, audio=b"ID3fake mp3")
    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google])
    monkeypatch.setattr(tts_mod, "_play_sound", MagicMock())

    tts_mod.speak("привет")

    mock_google.synthesize.assert_called_with("привет")


def test_speak_fallback_to_piper(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=False)
    mock_piper = _make_mock_provider(is_cloud=False, available=True, audio=b"RIFFwav")

    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google, mock_piper])
    monkeypatch.setattr(tts_mod, "_play_bytes", MagicMock())

    tts_mod.speak("привет")

    mock_google.synthesize.assert_not_called()
    mock_piper.synthesize.assert_called_with("привет")


def test_speak_fallback_on_exception(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=True)
    mock_google.synthesize.side_effect = Exception("network error")

    mock_piper = _make_mock_provider(is_cloud=False, available=True, audio=b"RIFFwav")

    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google, mock_piper])
    monkeypatch.setattr(tts_mod, "_play_bytes", MagicMock())

    tts_mod.speak("привет")

    mock_google.synthesize.assert_called_once()
    mock_piper.synthesize.assert_called_once()


def test_speak_all_fail_makes_error_sound(monkeypatch):
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=False)
    mock_piper = _make_mock_provider(is_cloud=False, available=False)

    mock_callback = MagicMock()
    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google, mock_piper])

    tts_mod.speak("привет", on_all_fail=mock_callback)

    mock_callback.assert_called_once()


def test_cloud_fixed_phrase_played(monkeypatch):
    """Cloud-провайдер: фиксированная фраза из ассетов играется без синтеза."""
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=True)
    mock_google.fixed_phrase.return_value = b"ID3fixed mp3"
    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google])
    fake_sound = MagicMock()
    monkeypatch.setattr(tts_mod, "_bytes_to_sound", lambda data: fake_sound)
    mock_play = MagicMock()
    monkeypatch.setattr(tts_mod, "_play_sound", mock_play)

    tts_mod.speak("Слушаю")

    mock_google.synthesize.assert_not_called()
    mock_google.fixed_phrase.assert_called_with("Слушаю")
    mock_play.assert_called_once_with(fake_sound)


def test_cloud_dynamic_cached_after_synth(monkeypatch):
    """Cloud-провайдер: после синтеза фраза кэшируется, второй раз — из кэша."""
    import voice_assistant.speech.tts as tts_mod

    mock_google = _make_mock_provider(is_cloud=True, available=True, audio=b"ID3dynamic")
    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_google])
    monkeypatch.setattr(tts_mod, "_play_sound", MagicMock())
    mock_sound = MagicMock()
    monkeypatch.setattr(tts_mod, "_bytes_to_sound", lambda data: mock_sound)

    tts_mod._dynamic_cache.clear()
    tts_mod.speak("Гомель, плюс 15")
    assert mock_google.synthesize.call_count == 1
    assert "Гомель, плюс 15" in tts_mod._dynamic_cache

    tts_mod.speak("Гомель, плюс 15")
    assert mock_google.synthesize.call_count == 1
    tts_mod._dynamic_cache.clear()


def test_local_provider_not_cached(monkeypatch):
    """Local-провайдер: синтез каждый раз, кэш не растёт."""
    import voice_assistant.speech.tts as tts_mod

    mock_piper = _make_mock_provider(is_cloud=False, available=True, audio=b"RIFFwav")
    monkeypatch.setattr(tts_mod, "_active_providers", lambda: [mock_piper])
    monkeypatch.setattr(tts_mod, "_play_bytes", MagicMock())

    tts_mod._dynamic_cache.clear()
    tts_mod.speak("Гомель, плюс 15")
    tts_mod.speak("Гомель, плюс 15")
    assert mock_piper.synthesize.call_count == 2
    assert len(tts_mod._dynamic_cache) == 0
    tts_mod._dynamic_cache.clear()


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


def test_google_tts_is_available_cached(monkeypatch):
    """is_available() кэширует результат на 60с — DNS-lookup один раз."""
    import socket

    from voice_assistant.speech.providers.google_tts import GoogleTTSProvider

    call_count = {"n": 0}

    def counting_dns(host):
        call_count["n"] += 1
        return "1.2.3.4"

    monkeypatch.setattr(socket, "gethostbyname", counting_dns)
    provider = GoogleTTSProvider()

    provider.is_available()
    provider.is_available()
    provider.is_available()
    assert call_count["n"] == 1
