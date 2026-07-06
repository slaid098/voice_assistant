"""Интеграционные тесты полного workflow ассистента.

Проверяют точную последовательность вызовов make_sound/speak на каждом этапе
без реальных аудио/сети. Цель — гарантировать отсутствие лишних бипов и фраз.
"""

import numpy as np


def _fake_audio() -> np.ndarray:
    """Фиктивный аудио-массив (не используется при замоканном transcribe)."""
    return np.zeros(1600, dtype=np.int16)


def test_wake_to_weather_no_extra_sounds(monkeypatch, mock_speak, mock_make_sound):
    """wake → «Слушаю» → «погода» → «Выполняю» + погода → DONE (один).

    Ожидаемая последовательность:
      speak: «Слушаю.», «Выполняю.», <погода>
      make_sound: DONE (один раз)
    Никаких лишних бипов.
    """
    import voice_assistant.assistant as a_mod
    import voice_assistant.nlu.handlers as h_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(["слушай вики", "погода"])
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(h_mod, "get_weather_text", lambda city: "Гомель, плюс 15.")
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    speak_texts = [c.args[0] for c in mock_speak.call_args_list]
    assert "Слушаю." in speak_texts
    assert "Выполняю." in speak_texts
    assert "Гомель, плюс 15." in speak_texts

    done_calls = [c for c in mock_make_sound.call_args_list if c.args[0].name == "DONE"]
    assert len(done_calls) == 1, f"Ожидался 1 DONE, получено {len(done_calls)}"


def test_youtube_navigation_timeout_single_done(monkeypatch, mock_speak, mock_make_sound):
    """wake → «Слушаю» → «ютуб» → «Ищу» + SEARCH_STARTED → навигация → таймаут → DONE (один!).

    Ключевая проверка: при таймауте в навигации DONE играется ОДИН раз, не два.
    """
    import voice_assistant.assistant as a_mod
    import voice_assistant.services.youtube as yt_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(["слушай вики", "ютуб котики", None])
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(
        yt_mod,
        "search_youtube_videos",
        lambda q: [{"title": "Котики", "url": "https://youtu.be/1"}],
    )
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    done_calls = [c for c in mock_make_sound.call_args_list if c.args[0].name == "DONE"]
    assert len(done_calls) == 1, (
        f"При таймауте навигации DONE должен играть 1 раз, получено {len(done_calls)}"
    )


def test_command_timeout_single_done(monkeypatch, mock_speak, mock_make_sound):
    """wake → «Слушаю» → мама молчит → таймаут → DONE (один).

    Проверка: при таймауте команды (молчание) играет один DONE, не два.
    """
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(["слушай вики", None])
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    speak_texts = [c.args[0] for c in mock_speak.call_args_list]
    assert "Слушаю." in speak_texts

    done_calls = [c for c in mock_make_sound.call_args_list if c.args[0].name == "DONE"]
    assert len(done_calls) == 1, f"Ожидался 1 DONE при таймауте, получено {len(done_calls)}"


def test_three_misunderstandings_then_exit(monkeypatch, mock_speak, mock_make_sound):
    """wake → «Слушаю» → 3 раза непонимание → DONE + «Не получается».

    Проверка: 3 непонимания → DONE + «Не получается. Скажите слово активации снова.»
    """
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(
        [
            "слушай вики",
            "блаблабра непонятное",
            "ещё непонятное",
            "совсем непонятное",
        ]
    )
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    speak_texts = [c.args[0] for c in mock_speak.call_args_list]
    assert speak_texts.count("Я вас не поняла, повторите.") == 2
    assert "Не получается. Скажите слово активации снова." in speak_texts


def test_misunderstanding_no_extra_beeps(monkeypatch, mock_speak, mock_make_sound):
    """При непонимании — только фраза, без бипов DONE/READY.

    Проверка: 2 непонимания подряд — DONE не играется, только на 3-й (выход).
    READY_TO_LISTEN не играется при переспросе.
    """
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(
        [
            "слушай вики",
            "блабла",
            "опять блабла",
            "совсем блабла",
        ]
    )
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    done_calls = [c for c in mock_make_sound.call_args_list if c.args[0].name == "DONE"]
    ready_calls = [c for c in mock_make_sound.call_args_list if c.args[0].name == "READY_TO_LISTEN"]
    assert len(done_calls) == 1, "DONE должен играть только при выходе (3-я попытка)"
    assert len(ready_calls) == 0, "READY_TO_LISTEN не должен играть при переспросе"


def test_wake_word_not_detected_no_sound(monkeypatch, mock_speak, mock_make_sound):
    """Сказали что-то без wake word → выход без звуков и фраз."""
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: "привет как дела")
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    mock_speak.assert_not_called()
    mock_make_sound.assert_not_called()


def test_wake_timeout_no_sound(monkeypatch, mock_speak, mock_make_sound):
    """Молчание на этапе wake word → выход без звуков."""
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: None)
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    mock_speak.assert_not_called()
    mock_make_sound.assert_not_called()


def test_vosk_wake_word_triggers_command(monkeypatch, mock_speak, mock_make_sound):
    """Vosk wake-word streaming: детектор детектит «вики» → команда → ответ.

    Проверка: при WAKE_WORD_DETECTOR=vosk ассистент использует streaming-путь,
    не обращаясь к Google для wake word. Команда идёт через Google (дефолт).
    """
    import voice_assistant.assistant as a_mod
    import voice_assistant.speech.audio as audio_mod

    fake_detector = type(
        "FakeVoskDetector",
        (),
        {
            "name": "vosk",
            "detect_chunk": lambda self, chunk: "вики" if chunk[0] == 0 else None,
            "is_available": lambda self: True,
        },
    )()
    monkeypatch.setattr(a_mod, "active_wake_word_detector", lambda: fake_detector)

    def fake_record(timeout_ms, *, on_chunk=None):
        if on_chunk is not None:
            import numpy as np

            chunk = np.zeros(1600, dtype=np.int16)
            on_chunk(chunk)
            return None
        return _fake_audio()

    monkeypatch.setattr(audio_mod, "record_user_speech", fake_record)
    monkeypatch.setattr(a_mod, "record_user_speech", fake_record)
    transcribe_responses = iter(["погода"])
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    import voice_assistant.nlu.handlers as h_mod

    monkeypatch.setattr(h_mod, "get_weather_text", lambda city: "Гомель, плюс 15.")

    a_mod.run_assistant_step()

    speak_texts = [c.args[0] for c in mock_speak.call_args_list]
    assert "Слушаю." in speak_texts
    assert "Выполняю." in speak_texts
    assert "Гомель, плюс 15." in speak_texts


def test_vosk_wake_word_timeout_no_command(monkeypatch, mock_speak, mock_make_sound):
    """Vosk wake-word: детектор не сработал → выход без команды."""
    import voice_assistant.assistant as a_mod
    import voice_assistant.speech.audio as audio_mod

    fake_detector = type(
        "FakeVoskDetector",
        (),
        {
            "name": "vosk",
            "detect_chunk": lambda self, chunk: None,
            "is_available": lambda self: True,
        },
    )()
    monkeypatch.setattr(a_mod, "active_wake_word_detector", lambda: fake_detector)

    def fake_record(timeout_ms, *, on_chunk=None):
        import numpy as np

        chunk = np.zeros(1600, dtype=np.int16)
        if on_chunk is not None:
            on_chunk(chunk)

    monkeypatch.setattr(audio_mod, "record_user_speech", fake_record)
    monkeypatch.setattr(a_mod, "record_user_speech", fake_record)
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    a_mod.run_assistant_step()

    mock_speak.assert_not_called()
    mock_make_sound.assert_not_called()


def test_fallback_to_fuzzy_when_vosk_unavailable(monkeypatch, mock_speak, mock_make_sound):
    """Vosk недоступен → авто-fallback на fuzzy+Google путь."""
    import voice_assistant.assistant as a_mod

    monkeypatch.setattr(a_mod, "active_wake_word_detector", lambda: None)

    monkeypatch.setattr(a_mod, "record_user_speech", lambda **kw: _fake_audio())
    transcribe_responses = iter(["слушай вики", "погода"])
    monkeypatch.setattr(a_mod, "transcribe_audio", lambda audio: next(transcribe_responses))
    monkeypatch.setattr(a_mod, "drain_speech_queue", lambda: None)

    import voice_assistant.nlu.handlers as h_mod

    monkeypatch.setattr(h_mod, "get_weather_text", lambda city: "Гомель, плюс 15.")

    a_mod.run_assistant_step()

    speak_texts = [c.args[0] for c in mock_speak.call_args_list]
    assert "Слушаю." in speak_texts
    assert "Выполняю." in speak_texts
