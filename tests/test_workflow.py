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
