from src.youtube import _clean_title


def test_clean_title():
    assert _clean_title("Клип [Официальный] - Песня (2020)!") == "Клип Песня !"
