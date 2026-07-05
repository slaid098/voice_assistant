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
