import threading
from datetime import datetime

from src.tts import speak


def handle_simple_command(intent_name: str, payload: str | None) -> None:
    """Routes simple commands to their respective text generators/runners."""
    if intent_name == "time":
        speak(_get_time_text())

    elif intent_name == "timer":
        _handle_timer(payload)

    elif intent_name == "help":
        _HELP_TEXT = (
            "Вот что я умею. "
            "Скажите Вики ютуб и запрос — я найду видео. "
            "Скажите Вики погода — расскажу погоду. "
            "Скажите Вики время — скажу текущее время. "
            "Скажите Вики таймер — поставлю таймер. "
            "Скажите Вики помощь — повторю команды."
        )
        speak(_HELP_TEXT)


def _get_time_text() -> str:
    """Generate datetime text."""
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")
    return f"Сегодня {date_str}, текущее время {time_str}"


def _handle_timer(payload: str | None) -> None:
    """Validate timer request, spawn alarm thread."""
    if not payload:
        speak("Укажите время для таймера. Например: таймер пять минут.")
        return

    seconds = _parse_timer_seconds(payload)
    if seconds is None:
        speak("Не расслышала время. Повторите, например: таймер пять минут.")
        return

    display = _format_timer_display(seconds)
    speak(f"Ставлю таймер на {display}.")

    def _on_timer_done() -> None:
        speak(f"Таймер на {display} истёк.")

    timer = threading.Timer(seconds, _on_timer_done)
    timer.daemon = True
    timer.start()


def _parse_timer_seconds(payload: str) -> int | None:
    """Extract timer seconds from string."""
    import re
    numbers = re.findall(r"\d+", payload)
    if not numbers:
        return None

    value = int(numbers[0])
    payload_lower = payload.lower()

    if "мин" in payload_lower:
        return value * 60
    if "сек" in payload_lower:
        return value
    if "час" in payload_lower:
        return value * 3600
    return value * 60


def _format_timer_display(total_seconds: int) -> str:
    """Humanize seconds into Russian words."""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours} {_plural(hours, ('час', 'часа', 'часов'))}")
    if minutes > 0:
        parts.append(f"{minutes} {_plural(minutes, ('минута', 'минуты', 'минут'))}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} {_plural(seconds, ('секунда', 'секунды', 'секунд'))}")
    return " ".join(parts)


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    n = abs(n)
    if 11 <= n % 100 <= 14:
        return forms[2]
    if n % 10 == 1:
        return forms[0]
    if 2 <= n % 10 <= 4:
        return forms[1]
    return forms[2]
