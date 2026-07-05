import dataclasses
from unittest.mock import MagicMock


def test_bytes_to_sound_loads_bytes(monkeypatch):
    """_bytes_to_sound создаёт Sound из байтов в памяти (без temp-файла)."""
    import voice_assistant.speech.tts as tts_mod

    fake_sound = MagicMock()
    mock_sound_cls = MagicMock(return_value=fake_sound)
    monkeypatch.setattr(tts_mod.pygame.mixer, "Sound", mock_sound_cls)

    result = tts_mod._bytes_to_sound(b"fake audio bytes")

    assert result is fake_sound
    mock_sound_cls.assert_called_once()


def test_bytes_to_sound_returns_none_on_exception(monkeypatch):
    """_bytes_to_sound возвращает None при ошибке pygame, без исключения."""
    import voice_assistant.speech.tts as tts_mod

    def raise_ex(data):
        raise RuntimeError("pygame error")

    monkeypatch.setattr(tts_mod.pygame.mixer, "Sound", raise_ex)

    result = tts_mod._bytes_to_sound(b"bad bytes")
    assert result is None


def test_play_sound_blocks_until_not_busy(monkeypatch):
    """_play_sound проигрывает и ждёт завершения."""
    import voice_assistant.speech.tts as tts_mod

    fake_sound = MagicMock()
    busy_states = iter([True, True, False])
    monkeypatch.setattr(tts_mod.pygame.mixer, "get_busy", lambda: next(busy_states))

    tts_mod._play_sound(fake_sound)

    fake_sound.play.assert_called_once()


def test_play_sound_exception_handled(monkeypatch):
    """_play_sound ловит исключения без падения."""
    import voice_assistant.speech.tts as tts_mod

    fake_sound = MagicMock()
    fake_sound.play.side_effect = RuntimeError("play error")
    monkeypatch.setattr(tts_mod.pygame.mixer, "get_busy", lambda: False)

    tts_mod._play_sound(fake_sound)


def test_play_bytes_delegates_to_bytes_to_sound(monkeypatch):
    """_play_bytes идёт через _bytes_to_sound → _play_sound (без temp-файла)."""
    import voice_assistant.speech.tts as tts_mod

    fake_sound = MagicMock()
    monkeypatch.setattr(tts_mod, "_bytes_to_sound", lambda data: fake_sound)
    mock_play = MagicMock()
    monkeypatch.setattr(tts_mod, "_play_sound", mock_play)

    tts_mod._play_bytes(b"audio")

    mock_play.assert_called_with(fake_sound)


def test_cache_dynamic_respects_limit(monkeypatch):
    """LRU-кэш не превышает лимит из settings.tts_cache_size."""
    import voice_assistant.speech.tts as tts_mod

    test_settings = dataclasses.replace(tts_mod.settings, tts_cache_size=3)
    monkeypatch.setattr(tts_mod, "settings", test_settings)
    tts_mod._dynamic_cache.clear()

    for i in range(5):
        sound = MagicMock()
        tts_mod._cache_dynamic(f"фраза {i}", sound)

    assert len(tts_mod._dynamic_cache) == 3
    assert "фраза 0" not in tts_mod._dynamic_cache
    assert "фраза 1" not in tts_mod._dynamic_cache
    assert "фраза 4" in tts_mod._dynamic_cache
    tts_mod._dynamic_cache.clear()


def test_cache_dynamic_lru_eviction_order(monkeypatch):
    """LRU выкидывает самую старую неиспользованную."""
    import voice_assistant.speech.tts as tts_mod

    test_settings = dataclasses.replace(tts_mod.settings, tts_cache_size=2)
    monkeypatch.setattr(tts_mod, "settings", test_settings)
    tts_mod._dynamic_cache.clear()

    s1, s2, s3 = MagicMock(), MagicMock(), MagicMock()
    tts_mod._cache_dynamic("а", s1)
    tts_mod._cache_dynamic("б", s2)

    tts_mod._lookup_dynamic_cache("а")

    tts_mod._cache_dynamic("в", s3)

    assert "а" in tts_mod._dynamic_cache
    assert "б" not in tts_mod._dynamic_cache
    assert "в" in tts_mod._dynamic_cache
    tts_mod._dynamic_cache.clear()
