from voice_assistant.nlu.wake_word import is_wake_word


def test_exact_wake_word():
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
    assert is_wake_word("виккики") is True


def test_case_insensitive():
    assert is_wake_word("Вики") is True
    assert is_wake_word("ВИКИ") is True
