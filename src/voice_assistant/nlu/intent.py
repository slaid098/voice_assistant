import re
from typing import Any

from thefuzz import fuzz

from voice_assistant.config import IntentRule, settings


def parse_voice_intent(text: str) -> dict[str, Any] | None:
    """Разбирает голосовую команду в структурированный интент.

    Args:
        text: Распознанный текст команды.

    Returns:
        Словарь {intent, payload, confidence} или None.
    """
    if not text:
        return None

    cleaned_text = _normalize_command_text(_strip_wake_word(text))
    if not cleaned_text:
        return None

    best_rule: IntentRule | None = None
    best_trigger = ""
    best_score = 0

    for rule in settings.intent_rules:
        for keyword in rule.keywords:
            if keyword in cleaned_text:
                score = 100
                trigger = keyword
            else:
                score = fuzz.ratio(keyword, cleaned_text)
                trigger = keyword

            if score >= rule.threshold and score > best_score:
                best_score = score
                best_rule = rule
                best_trigger = trigger

    if best_rule is None:
        return None

    payload = _extract_payload(cleaned_text, best_trigger, best_rule)
    return {
        "intent": best_rule.intent.value,
        "payload": payload,
        "confidence": best_score,
    }


def _strip_wake_word(text: str) -> str:
    """Удаляет wake-слова и мусорные слова из текста."""
    words = text.lower().strip().split()
    cleaned_words = []

    for word in words:
        clean_word = re.sub(r"[^\w\sА-Яа-яЁё]", "", word)
        if clean_word in settings.wake_aliases or clean_word in settings.junk_words:
            continue
        cleaned_words.append(word)

    return " ".join(cleaned_words).strip()


def _extract_payload(text: str, trigger: str, rule: IntentRule) -> str | None:
    """Удаляет триггер-слово и возвращает payload."""
    if not rule.has_payload:
        return None

    text_lower = text.lower()
    trigger_lower = trigger.lower()

    raw = text_lower.replace(trigger_lower, "", 1).strip()
    if raw == text_lower:
        for word in trigger_lower.split():
            raw = raw.replace(word, "", 1).strip()

    words = raw.split()
    while words and (
        str(words[0]).lower() in settings.junk_words or str(words[0]).lower() in settings.cmd_junk
    ):
        words.pop(0)

    result = " ".join(words).strip()
    return result or None


def _normalize_command_text(text: str) -> str:
    """Нормализует латинские алиасы для стабильного матчинга интентов."""
    normalized = text.lower()
    aliases = {
        "youtube": "ютуб",
        "you tube": "ютуб",
        "ютюб": "ютуб",
    }
    for source, target in aliases.items():
        normalized = normalized.replace(source, target)
    return normalized
