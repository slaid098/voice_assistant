from collections.abc import Callable
from typing import Protocol

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


class SimpleCommandHandler:
    def __init__(self, intent: str) -> None:
        self._intent = intent

    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        handle_simple_command(self._intent, payload)


class YouTubeSearchHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        run_youtube_flow(payload, listen=listen)


class StopHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        speak("Ушла спать.")


class NowPlayingHandler:
    def execute(self, payload: str | None, *, listen: ListenFn) -> None:
        title = get_current_title()
        if title:
            speak(f"Сейчас играет: {title}")
        else:
            speak("Сейчас ничего не играет.")


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
    from loguru import logger

    logger.warning(f"Unknown intent: {intent_name}")
    speak("Я не знаю такую команду.")