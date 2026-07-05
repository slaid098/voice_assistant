from thefuzz import fuzz

from voice_assistant.config import settings


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
    return any(_matches_wake_word(word) for word in words)


def _matches_wake_word(word: str) -> bool:
    """Проверяет одно слово против wake word и алиасов."""
    if settings.wake_word in word:
        return True

    for alias in settings.wake_aliases:
        if alias in word:
            return True
        if fuzz.ratio(alias, word) >= settings.wake_threshold:
            return True

    root = settings.wake_word[:3] if len(settings.wake_word) >= 3 else settings.wake_word
    return root in word