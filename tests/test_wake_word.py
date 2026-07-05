from voice_assistant.nlu.wake_word import is_wake_word


def test_exact_default_wake_word():
    """Default wake word is 'вики' when WAKE_WORD env is not set."""
    assert is_wake_word("вики") is True


def test_wake_word_in_sentence():
    assert is_wake_word("привет вики погода") is True


def test_fuzzy_wake_word_vike():
    assert is_wake_word("вике") is True


def test_fuzzy_wake_word_vika():
    assert is_wake_word("вика") is True


def test_fuzzy_wake_word_vikki():
    assert is_wake_word("викки") is True


def test_not_wake_word():
    assert is_wake_word("привет") is False


def test_not_wake_word_empty():
    assert is_wake_word("") is False


def test_not_wake_word_unrelated():
    assert is_wake_word("погода москва") is False


def test_root_match():
    """Root 'вик' should match words containing it."""
    assert is_wake_word("виккики") is True


def test_case_insensitive():
    assert is_wake_word("Вики") is True
    assert is_wake_word("ВИКИ") is True


def test_custom_wake_word_from_env(monkeypatch):
    """Wake word is configurable via WAKE_WORD env."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    custom = dataclasses.replace(
        config_mod._load_settings(),
        wake_word="маркиза",
        wake_aliases=["маркиза"],
    )
    monkeypatch.setattr(ww_mod, "settings", custom)

    assert ww_mod.is_wake_word("маркиза") is True
    assert ww_mod.is_wake_word("вики") is False


def test_check_wake_word_fuzzy_match():
    """_check_wake_word_fuzzy распознаёт точное совпадение."""
    from voice_assistant.nlu.wake_word import _check_wake_word_fuzzy

    assert _check_wake_word_fuzzy("вики") == "вики"
    assert _check_wake_word_fuzzy("вика") == "вика"


def test_check_wake_word_fuzzy_unk_returns_none():
    """_check_wake_word_fuzzy возвращает None для [unk]."""
    from voice_assistant.nlu.wake_word import _check_wake_word_fuzzy

    assert _check_wake_word_fuzzy("[unk]") is None
    assert _check_wake_word_fuzzy("") is None


def test_check_wake_word_fuzzy_unrelated_returns_none():
    """_check_wake_word_fuzzy отсекает неродственные слова."""
    from voice_assistant.nlu.wake_word import _check_wake_word_fuzzy

    assert _check_wake_word_fuzzy("привет") is None
    assert _check_wake_word_fuzzy("погода") is None


def test_build_grammar_contains_wake_aliases():
    """_build_grammar собирает JSON из wake_aliases + [unk]."""
    import json

    from voice_assistant.nlu.wake_word import _build_grammar

    grammar = json.loads(_build_grammar())
    assert "[unk]" in grammar
    assert "вики" in grammar
    assert "вика" in grammar


def test_active_detector_fuzzy_when_vosk_unavailable(monkeypatch):
    """При WAKE_WORD_DETECTOR=vosk и недоступной модели — fallback на fuzzy (None)."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="vosk")
    monkeypatch.setattr(ww_mod, "settings", settings)

    monkeypatch.setattr(ww_mod.VoskWakeWordDetector, "is_available", lambda self: False)

    detector = ww_mod.active_wake_word_detector()
    assert detector is None


def test_active_detector_returns_vosk_when_available(monkeypatch):
    """При WAKE_WORD_DETECTOR=vosk и доступной модели — VoskWakeWordDetector."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="vosk")
    monkeypatch.setattr(ww_mod, "settings", settings)
    monkeypatch.setattr(ww_mod.VoskWakeWordDetector, "is_available", lambda self: True)

    detector = ww_mod.active_wake_word_detector()
    assert detector is not None
    assert detector.name == "vosk"


def test_active_detector_fuzzy_mode(monkeypatch):
    """При WAKE_WORD_DETECTOR=fuzzy — FuzzyWakeWordDetector."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="fuzzy")
    monkeypatch.setattr(ww_mod, "settings", settings)

    detector = ww_mod.active_wake_word_detector()
    assert detector is not None
    assert detector.name == "fuzzy"


def test_vosk_detector_detects_wake_word(monkeypatch):
    """VoskWakeWordDetector.detect_chunk детектит wake word через мок recognizer."""
    import json

    from voice_assistant.nlu.wake_word import VoskWakeWordDetector

    fake_recognizer = type(
        "FakeRecognizer",
        (),
        {
            "accept_waveform": lambda self, data: 1,
            "result": lambda self: json.dumps({"text": "вики"}),
            "partial_result": lambda self: json.dumps({"partial": ""}),
        },
    )()

    detector = VoskWakeWordDetector()
    monkeypatch.setattr(detector, "_ensure_loaded", lambda: fake_recognizer)

    import numpy as np

    chunk = np.zeros(1600, dtype=np.int16)
    result = detector.detect_chunk(chunk)
    assert result == "вики"


def test_vosk_detector_ignores_unk(monkeypatch):
    """VoskWakeWordDetector игнорирует [unk] (ложное срабатывание)."""
    import json

    from voice_assistant.nlu.wake_word import VoskWakeWordDetector

    fake_recognizer = type(
        "FakeRecognizer",
        (),
        {
            "accept_waveform": lambda self, data: 1,
            "result": lambda self: json.dumps({"text": "[unk]"}),
            "partial_result": lambda self: json.dumps({"partial": ""}),
        },
    )()

    detector = VoskWakeWordDetector()
    monkeypatch.setattr(detector, "_ensure_loaded", lambda: fake_recognizer)

    import numpy as np

    chunk = np.zeros(1600, dtype=np.int16)
    result = detector.detect_chunk(chunk)
    assert result is None
