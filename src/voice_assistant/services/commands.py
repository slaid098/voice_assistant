import queue
import re
import threading
from datetime import datetime

from loguru import logger

from voice_assistant.speech.tts import speak

_speech_queue: queue.Queue[str] = queue.Queue()


class _TimerState:
    """Управляет активным таймером."""

    def __init__(self) -> None:
        self._active_timer: threading.Timer | None = None

    def set(self, timer: threading.Timer) -> None:
        """Устанавливает новый таймер, отменяя предыдущий."""
        self.cancel()
        self._active_timer = timer

    def cancel(self) -> bool:
        """Отменяет активный таймер. Возвращает True, если был активный."""
        if self._active_timer is None:
            return False
        self._active_timer.cancel()
        self._active_timer = None
        logger.info("Активный таймер отменён")
        return True

    def clear(self) -> None:
        """Очищает ссылку (после срабатывания)."""
        self._active_timer = None


_timer_state = _TimerState()


def drain_speech_queue() -> None:
    """Вызывается из main loop — озвучивает все накопленные сообщения от timer."""
    while True:
        try:
            text = _speech_queue.get_nowait()
        except queue.Empty:
            break
        speak(text)


def cancel_timer() -> None:
    """Отменяет активный таймер (если есть)."""
    _timer_state.cancel()


def handle_simple_command(intent_name: str, payload: str | None) -> None:
    """Маршрутизирует простые команды к их обработчикам."""
    if intent_name == "time":
        speak(_get_time_text())

    elif intent_name == "timer":
        _handle_timer(payload)

    elif intent_name == "help":
        _help_text = (
            "Вот что я умею. "
            "Скажите ютуб и запрос — я найду видео. "
            "Скажите погода — расскажу погоду. "
            "Скажите время — скажу текущее время. "
            "Скажите таймер — поставлю таймер. "
            "Скажите название — скажу, что сейчас играет. "
            "Скажите стоп — отменю таймер."
        )
        speak(_help_text)

    elif intent_name == "stop":
        cancel_timer()


def _get_time_text() -> str:
    """Возвращает текущую дату и время."""
    now = datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    time_str = now.strftime("%H:%M")
    return f"Сегодня {date_str}, текущее время {time_str}"


def _handle_timer(payload: str | None) -> None:
    """Ставит таймер (daemon thread, озвучка через queue).

    Если уже есть активный таймер — отменяет его.
    """
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
        _timer_state.clear()
        _speech_queue.put(f"Таймер на {display} истёк.")

    timer = threading.Timer(seconds, _on_timer_done)
    timer.daemon = True
    timer.start()
    _timer_state.set(timer)


def _parse_timer_seconds(payload: str) -> int | None:
    """Извлекает секунды из строки таймера."""
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
    """Превращает секунды в человекочитаемый текст."""
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
    """Выбирает правильную форму слова по числу."""
    n = abs(n)
    if 11 <= n % 100 <= 14:
        return forms[2]
    if n % 10 == 1:
        return forms[0]
    if 2 <= n % 10 <= 4:
        return forms[1]
    return forms[2]
