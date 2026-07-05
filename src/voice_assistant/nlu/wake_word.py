from thefuzz import fuzz

from voice_assistant.config import WAKE_ALIASES, WAKE_THRESHOLD, WAKE_WORD


def is_wake_word(text: str) -> bool:
    """Проверяет, содержит ли фраза слово активации (fuzzy-матчинг).

    Args:
        text: Распознанная фраза пользователя.

    Returns:
        True, если слово активации найдено.
    """
    if not text:
        return False

    words = text.lower().strip().split()
    for word in words:
        if _matches_wake_word(word):
            return True
    return False


def _matches_wake_word(word: str) -> bool:
    """Проверяет одно слово против wake word и алиасов."""
    if WAKE_WORD in word:
        return True

    for alias in WAKE_ALIASES:
        if alias in word:
            return True
        if fuzz.ratio(alias, word) >= WAKE_THRESHOLD:
            return True

    root = WAKE_WORD[:3] if len(WAKE_WORD) >= 3 else WAKE_WORD
    if root in word:
        return True

    return False