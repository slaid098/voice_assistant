from collections.abc import Callable
from typing import Protocol

from loguru import logger

from voice_assistant.audio.sounds import Sound, make_sound
from voice_assistant.config import Intent
from voice_assistant.services.browser import get_current_title
from voice_assistant.services.commands import handle_simple_command
from voice_assistant.services.weather import get_weather_text
from voice_assistant.services.youtube_flow import run_youtube_flow
from voice_assistant.speech.tts import speak

ListenFn = Callable[..., str | None]


class IntentHandler(Protocol):
    """Интерфейс обработчика интента."""

    def execute(self, payload: str | None, *, listen: ListenFn) -> None: ...


class WeatherHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        speak(get_weather_text(payload))
        make_sound(Sound.DONE)


class SimpleCommandHandler:
    def __init__(self, intent: str) -> None:
        self._intent = intent

    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        handle_simple_command(self._intent, payload)
        make_sound(Sound.DONE)


class YouTubeSearchHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        run_youtube_flow(payload, listen=listen)
        make_sound(Sound.DONE)


class StopHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        speak("Нечего отменять.")
        make_sound(Sound.DONE)


class NowPlayingHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        title = get_current_title()
        if title:
            speak(f"Сейчас играет: {title}")
        else:
            speak("Сейчас ничего не играет.")
        make_sound(Sound.DONE)


_HANDLERS: dict[str, IntentHandler] = {
    Intent.WEATHER.value: WeatherHandler(),
    Intent.TIME.value: SimpleCommandHandler(Intent.TIME.value),
    Intent.TIMER.value: SimpleCommandHandler(Intent.TIMER.value),
    Intent.HELP.value: SimpleCommandHandler(Intent.HELP.value),
    Intent.YOUTUBE_SEARCH.value: YouTubeSearchHandler(),
    Intent.STOP.value: StopHandler(),
    Intent.NOW_PLAYING.value: NowPlayingHandler(),
}


def execute_intent(intent_name: str, payload: str | None, *, listen: ListenFn) -> None:
    """Выполняет распознанный интент через strategy dispatch.

    Args:
        intent_name: Название интента.
        payload: Дополнительные параметры.
        listen: Функция прослушивания для YouTube flow.
    """
    handler = _HANDLERS.get(intent_name)
    if handler is None:
        logger_unknown_intent(intent_name)
        return
    handler.execute(payload, listen=listen)


def logger_unknown_intent(intent_name: str) -> None:
    logger.warning(f"Неизвестный интент: {intent_name}")
    speak("Я не знаю такую команду.")
