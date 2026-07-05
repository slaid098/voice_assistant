from loguru import logger

from voice_assistant.config import COMMAND_TIMEOUT_MS, WAKE_TIMEOUT_MS
from voice_assistant.nlu.intent import parse_voice_intent
from voice_assistant.nlu.wake_word import is_wake_word
from voice_assistant.services.browser import open_browser_url
from voice_assistant.services.commands import handle_simple_command
from voice_assistant.services.weather import get_weather_text
from voice_assistant.services.youtube import search_youtube_videos
from voice_assistant.speech.audio import record_user_speech
from voice_assistant.speech.stt import transcribe_audio
from voice_assistant.speech.tts import speak


def run_assistant_step() -> None:
    print("\n--- Ожидание активации... ---")
    activation_text = _listen_text_or_none(timeout_ms=WAKE_TIMEOUT_MS, stage="activation")
    if not activation_text:
        return
    if not is_wake_word(activation_text):
        return

    speak("Слушаю.")
    intent = _listen_intent_after_activation()
    if intent is None:
        return

    _execute_intent(intent_name=intent["intent"], payload=intent.get("payload"))


def _listen_intent_after_activation() -> dict | None:
    while True:
        command_text = _record_and_transcribe_with_retries(stage="command")
        if not command_text:
            return None

        intent = parse_voice_intent(command_text)
        if intent:
            return intent

        speak("Я вас не поняла, повторите.")


def _execute_intent(intent_name: str, payload: str | None) -> None:
    if intent_name == "weather":
        weather_info = get_weather_text(payload)
        speak(weather_info)
    elif intent_name in {"time", "timer", "help"}:
        handle_simple_command(intent_name, payload)
    elif intent_name == "youtube_search":
        _run_youtube_flow(payload)
    elif intent_name == "stop":
        speak("Ушла спать.")


def _listen_text_or_none(timeout_ms: int, stage: str) -> str | None:
    audio = record_user_speech(timeout_ms=timeout_ms)
    if audio is None:
        return None

    text = transcribe_audio(audio)
    if text:
        logger.info(f"[recognized:{stage}] {text}")
    return text


def _record_and_transcribe_with_retries(stage: str, prompt: str | None = None) -> str | None:
    while True:
        if prompt:
            speak(prompt)

        text = _listen_text_or_none(timeout_ms=COMMAND_TIMEOUT_MS, stage=stage)
        if text is None:
            speak("Ушла спать.")
            return None
        if text:
            return text

        speak("Я вас не поняла, повторите.")


def _run_youtube_flow(initial_query: str | None) -> None:
    query = initial_query
    if not query:
        query = _record_and_transcribe_with_retries(stage="youtube_query", prompt="Что найти?")
    if not query:
        return

    speak("Ищу.")
    videos = search_youtube_videos(query)
    if not videos:
        speak("Ничего не найдено.")
        return

    _run_youtube_pagination(videos=videos, query=query)


def _run_youtube_pagination(videos: list[dict], query: str) -> None:
    index = 0
    while True:
        video = videos[index]
        prompt = _build_video_prompt(query=query, title=video["title"], index=index)
        response = _record_and_transcribe_with_retries(stage="youtube_navigation", prompt=prompt)
        if not response:
            return

        action = _parse_pagination_response(response)
        if action == "play":
            _play_video(video["url"])
            return
        if action == "stop":
            speak("Поиск отменён.")
            return

        next_index = _get_next_index(index=index, action=action, total=len(videos))
        if next_index is None:
            speak("Не поняла. Скажите: включить, дальше или назад.")
            continue
        index = next_index


def _build_video_prompt(query: str, title: str, index: int) -> str:
    num_word = _number_to_russian_ordinal(index + 1)
    if index == 0:
        return (
            f"Вот что я нашла по запросу {query}. "
            f"Видео номер {num_word}: {title}. Включить или дальше?"
        )
    return f"Видео номер {num_word}: {title}. Включить или дальше?"


def _play_video(url: str) -> None:
    speak("Включаю.")
    open_browser_url(url)
    speak("Сделано.")


def _get_next_index(index: int, action: str, total: int) -> int | None:
    if action == "next":
        if index + 1 < total:
            return index + 1
        speak("Это последнее видео. Скажите: включить, назад или стоп.")
        return index

    if action == "back":
        if index > 0:
            return index - 1
        speak("Это первое видео. Скажите: включить, дальше или стоп.")
        return index

    return None


def _parse_pagination_response(text: str) -> str:
    text_lower = text.lower()

    play_words = {"включить", "включай", "давай", "это", "запусти", "давай это"}
    next_words = {"дальше", "следующее", "вперед", "вперёд", "пропусти"}
    back_words = {"назад", "предыдущее"}
    stop_words = {"стоп", "отмена", "хватит", "остановись"}

    for w in play_words:
        if w in text_lower:
            return "play"
    for w in next_words:
        if w in text_lower:
            return "next"
    for w in back_words:
        if w in text_lower:
            return "back"
    for w in stop_words:
        if w in text_lower:
            return "stop"

    return "unknown"


def _number_to_russian_ordinal(num: int) -> str:
    from num2words import num2words

    return num2words(num, lang="ru")