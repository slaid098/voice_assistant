import sys
import traceback
from datetime import datetime

from loguru import logger

from src.audio import record_user_speech
from src.browser import open_browser_url
from src.commands import handle_simple_command
from src.intent import parse_voice_intent
from src.stt import transcribe_audio
from src.tts import speak
from src.weather import get_weather_text
from src.youtube import search_youtube_videos

_ACTIVATION_WORD = "вики"
_ACTIVATION_TIMEOUT_MS = 3000
_COMMAND_TIMEOUT_MS = 6000


def run_assistant_step() -> None:
    """Выполняет один шаг ассистента от активации до ответа."""
    print("\n--- Ожидание активации... ---")
    activation_text = _listen_text_or_none(timeout_ms=_ACTIVATION_TIMEOUT_MS, stage="activation")
    if not activation_text:
        return
    if not _has_activation_word(activation_text):
        return

    speak("Слушаю.")
    intent = _listen_intent_after_activation()
    if intent is None:
        return

    _execute_intent(intent_name=intent["intent"], payload=intent.get("payload"))


def _listen_intent_after_activation() -> dict | None:
    """Слушает команды после активации, пока не получит валидный интент.

    Returns:
        Распознанный интент или None при таймауте.

    """
    while True:
        command_text = _record_and_transcribe_with_retries(stage="command")
        if not command_text:
            return None

        intent = parse_voice_intent(command_text)
        if intent:
            return intent

        speak("Я вас не поняла, повторите.")


def _execute_intent(intent_name: str, payload: str | None) -> None:
    """Исполняет распознанный интент.

    Args:
        intent_name: Название распознанного интента.
        payload: Дополнительные параметры команды.

    """
    if intent_name == "weather":
        weather_info = get_weather_text()
        speak(weather_info)
    elif intent_name in {"time", "timer", "help"}:
        handle_simple_command(intent_name, payload)
    elif intent_name == "youtube_search":
        _run_youtube_flow(payload)
    elif intent_name == "stop":
        speak("Ушла спать.")


def _has_activation_word(text: str) -> bool:
    """Проверяет, что фраза содержит слово активации.

    Args:
        text: Распознанная фраза пользователя.

    Returns:
        True, если есть слово активации.

    """
    return _ACTIVATION_WORD in text.lower()


def _listen_text_or_none(timeout_ms: int, stage: str) -> str | None:
    """Слушает микрофон и возвращает распознанный текст.

    Args:
        timeout_ms: Таймаут ожидания речи в миллисекундах.
        stage: Этап сценария для логов.

    Returns:
        Распознанный текст или None.

    """
    audio = record_user_speech(timeout_ms=timeout_ms)
    if audio is None:
        return None

    text = transcribe_audio(audio)
    if text:
        logger.info(f"[recognized:{stage}] {text}")
    return text


def _record_and_transcribe_with_retries(stage: str, prompt: str | None = None) -> str | None:
    """Повторно слушает и распознает речь до успеха или таймаута.

    Args:
        stage: Этап сценария для логов.
        prompt: Текст, который нужно озвучить перед ожиданием ответа.

    Returns:
        Распознанный текст или None, если пользователь молчит.

    """
    while True:
        if prompt:
            speak(prompt)

        text = _listen_text_or_none(timeout_ms=_COMMAND_TIMEOUT_MS, stage=stage)
        if text is None:
            speak("Ушла спать.")
            return None
        if text:
            return text

        speak("Я вас не поняла, повторите.")


def _run_youtube_flow(initial_query: str | None) -> None:
    """Ведет пользователя по сценарию поиска и выбора YouTube-видео."""
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
    """Озвучивает результаты YouTube и обрабатывает команды навигации."""
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
    """Формирует озвучку карточки видео.

    Args:
        query: Текст поискового запроса.
        title: Заголовок видео.
        index: Индекс текущего видео.

    Returns:
        Готовый текст подсказки для TTS.

    """
    num_word = _number_to_russian_ordinal(index + 1)
    if index == 0:
        return (
            f"Вот что я нашла по запросу {query}. "
            f"Видео номер {num_word}: {title}. Включить или дальше?"
        )
    return f"Видео номер {num_word}: {title}. Включить или дальше?"


def _play_video(url: str) -> None:
    """Открывает выбранное видео и подтверждает действие.

    Args:
        url: Ссылка на видео.

    """
    speak("Включаю.")
    open_browser_url(url)
    speak("Сделано.")


def _get_next_index(index: int, action: str, total: int) -> int | None:
    """Считает следующий индекс в выдаче YouTube.

    Args:
        index: Текущий индекс.
        action: Команда пользователя.
        total: Количество видео.

    Returns:
        Новый индекс, если переход возможен. Иначе None.

    """
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
    """Разбирает ответ в режиме навигации по YouTube."""
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
    """Преобразует порядковый номер для озвучки."""
    ordinals = {
        1: "один",
        2: "два",
        3: "три",
        4: "четыре",
        5: "пять",
        6: "шесть",
        7: "семь",
        8: "восемь",
        9: "девять",
        10: "десять",
    }
    return ordinals.get(num, str(num))


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    log_file = f"viki_{datetime.now():%Y-%m-%d}.log"
    logger.add(log_file, level="DEBUG", rotation="10 MB", retention=7, encoding="utf-8")


def _crash_handler(exc_type, exc_value, exc_tb) -> None:
    logger.critical("Необработанное исключение", exc_info=(exc_type, exc_value, exc_tb))
    print(f"\n{'='*60}", file=sys.stderr)
    print("КРИТИЧЕСКАЯ ОШИБКА: Ассистент аварийно завершил работу.", file=sys.stderr)
    print("".join(traceback.format_exception(exc_type, exc_value, exc_tb)), file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    input("\nНажмите Enter, чтобы закрыть окно...")


def main() -> None:
    """Запускает бесконечный цикл голосового ассистента."""
    _setup_logging()
    sys.excepthook = _crash_handler

    print("=== Ассистент Вики запущен ===")
    while True:
        try:
            run_assistant_step()
        except KeyboardInterrupt:
            print("\nЗавершение по Ctrl+C...")
            break
        except Exception as ex:
            tb = traceback.format_exc()
            logger.bind(error=ex, error_type=type(ex).__name__).error(f"Ошибка шага ассистента\n{tb}")
            print(f"\n[ОШИБКА] {type(ex).__name__}: {ex}", file=sys.stderr)
            print("Подробности в лог-файле.", file=sys.stderr)


if __name__ == "__main__":
    main()
    input("Нажмите Enter, чтобы закрыть окно...")
