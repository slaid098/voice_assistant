import queue
import re
import threading
from datetime import datetime

from num2words import num2words

from voice_assistant.speech.tts import speak

_MONTHS_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

_DAYS_ORDINAL_NEUTER = [
    "первое",
    "второе",
    "третье",
    "четвёртое",
    "пятое",
    "шестое",
    "седьмое",
    "восьмое",
    "девятое",
    "десятое",
    "одиннадцатое",
    "двенадцатое",
    "тринадцатое",
    "четырнадцатое",
    "пятнадцатое",
    "шестнадцатое",
    "семнадцатое",
    "восемнадцатое",
    "девятнадцатое",
    "двадцатое",
    "двадцать первое",
    "двадцать второе",
    "двадцать третье",
    "двадцать четвёртое",
    "двадцать пятое",
    "двадцать шестое",
    "двадцать седьмое",
    "двадцать восьмое",
    "двадцать девятое",
    "тридцатое",
    "тридцать первое",
]

_FEMININE_NUMBERS: dict[str, str] = {"один": "одна", "два": "две"}

_speech_queue: queue.Queue[str] = queue.Queue()


class _TimerState:
    """Управляет активным таймером. Новый таймер перезаписывает старый."""

    def __init__(self) -> None:
        self._active_timer: threading.Timer | None = None

    def set(self, timer: threading.Timer) -> None:
        """Устанавливает новый таймер, отменяя предыдущий."""
        if self._active_timer is not None:
            self._active_timer.cancel()
        self._active_timer = timer

    def clear(self) -> None:
        """Очищает ссылку (после естественного срабатывания)."""
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
            "Во время поиска скажите стоп — отменю поиск. "
            "Скажите погода — расскажу погоду. "
            "Скажите время — скажу текущее время. "
            "Скажите таймер — поставлю таймер. "
            "Скажите название — скажу, что сейчас играет."
        )
        speak(_help_text)


def _get_time_text() -> str:
    """Возвращает текущую дату и время естественной русской речью.

    Формат: «Сегодня шестое июля, двадцать часов пятнадцать минут» — без точек,
    двоеточий и цифр, которые TTS читал бы буквально как «точка», «двоеточие».
    """
    now = datetime.now()
    day = _DAYS_ORDINAL_NEUTER[now.day - 1]
    month = _MONTHS_GENITIVE[now.month - 1]
    hours_word = _plural(now.hour, ("час", "часа", "часов"))
    time_str = f"{num2words(now.hour, lang='ru')} {hours_word}"
    if now.minute:
        minutes_word = _plural(now.minute, ("минута", "минуты", "минут"))
        time_str += f" {_num2words_feminine(now.minute)} {minutes_word}"
    return f"Сегодня {day} {month}, {time_str}"


def _num2words_feminine(n: int) -> str:
    """Число в женском роде (для слов «минута», «секунда»).

    num2words всегда возвращает мужской род («один», «два»). Для минут нужна
    женская форма («одна минута», «две минуты»).
    """
    word = str(num2words(n, lang="ru"))
    parts = word.rsplit(" ", 1)
    if len(parts) == 2:
        prefix, last = parts
        return f"{prefix} {_FEMININE_NUMBERS.get(last, last)}"
    return _FEMININE_NUMBERS.get(word, word)


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
