from loguru import logger

from voice_assistant.audio.sounds import Sound, make_sound
from voice_assistant.config import settings
from voice_assistant.services.browser import open_browser_url
from voice_assistant.services.youtube import search_youtube_videos
from voice_assistant.speech.tts import speak

_PAGINATION_WORDS: dict[str, set[str]] = {
    "play": {"включить", "включай", "давай", "это", "запусти", "давай это"},
    "next": {"дальше", "следующее", "вперед", "вперёд", "пропусти"},
    "back": {"назад", "предыдущее"},
    "stop": {"стоп", "отмена", "хватит", "остановись"},
}


def run_youtube_flow(
    initial_query: str | None,
    *,
    listen: object,
) -> None:
    """Ведёт пользователя по сценарию поиска и выбора YouTube-видео.

    Args:
        initial_query: Запрос из голосовой команды (может быть None).
        listen: Функция listen(stage, prompt) -> str | None для записи+распознавания.
    """
    query = initial_query
    if not query:
        query = listen(stage="youtube_query", prompt="Что найти?")
    if not query:
        return

    speak("Ищу.")
    make_sound(Sound.SEARCH_STARTED)
    videos = search_youtube_videos(query)
    if not videos:
        speak("Ничего не найдено.")
        return

    _run_pagination(videos=videos, query=query, listen=listen)


def _run_pagination(
    videos: list[dict],
    query: str,
    *,
    listen: object,
) -> None:
    """Озвучивает результаты YouTube и обрабатывает команды навигации."""
    index = 0
    while True:
        video = videos[index]
        prompt = _build_video_prompt(query=query, title=video["title"], index=index)
        response = listen(stage="youtube_navigation", prompt=prompt)
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
    """Формирует озвучку карточки видео."""
    from num2words import num2words

    num_word = num2words(index + 1, lang="ru")
    if index == 0:
        return (
            f"Вот что я нашла по запросу {query}. "
            f"Видео номер {num_word}: {title}. Включить или дальше?"
        )
    return f"Видео номер {num_word}: {title}. Включить или дальше?"


def _play_video(url: str) -> None:
    """Открывает выбранное видео и подтверждает действие."""
    speak("Включаю.")
    open_browser_url(url)
    speak("Сделано.")


def _get_next_index(index: int, action: str, total: int) -> int | None:
    """Считает следующий индекс в выдаче YouTube."""
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
    for action, words in _PAGINATION_WORDS.items():
        for w in words:
            if w in text_lower:
                return action
    return "unknown"