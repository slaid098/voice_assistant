"""Тест: каждый пользовательский интент озвучен в help-тексте.

Если кто-то добавит новый интент — тест упадёт, пока не добавит keyword
в маппинг. Страхует от ситуации когда новая фича есть, но не озвучена.
"""

from voice_assistant.config import Intent
from voice_assistant.services.commands import _get_help_text

INTENT_KEYWORDS: dict[Intent, str] = {
    Intent.YOUTUBE_SEARCH: "ютуб",
    Intent.WEATHER: "погода",
    Intent.TIME: "время",
    Intent.TIMER: "таймер",
    Intent.NOW_PLAYING: "название",
}


def test_all_user_intents_announced_in_help() -> None:
    help_text = _get_help_text().lower()
    for intent, keyword in INTENT_KEYWORDS.items():
        assert keyword in help_text, (
            f"Интент {intent.name} не озвучен в help. "
            f"Добавь ключевое слово '{keyword}' в help-текст."
        )


def test_no_extra_intents_without_keyword() -> None:
    """Все пользовательские интенты (кроме STOP, HELP, UNKNOWN) должны быть в маппинге."""
    skip = {Intent.STOP, Intent.HELP, Intent.UNKNOWN}
    user_intents = set(Intent) - skip
    mapped = set(INTENT_KEYWORDS.keys())
    assert user_intents == mapped, (
        f"Расхождение: {user_intents ^ mapped}. Добавь новый интент в INTENT_KEYWORDS или skip."
    )
