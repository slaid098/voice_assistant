from typing import Any

from loguru import logger

from voice_assistant.audio.sounds import Sound, make_sound
from voice_assistant.config import settings
from voice_assistant.nlu.handlers import execute_intent
from voice_assistant.nlu.intent import parse_voice_intent
from voice_assistant.nlu.wake_word import active_wake_word_detector, is_wake_word
from voice_assistant.services.commands import drain_speech_queue
from voice_assistant.speech.audio import record_user_speech
from voice_assistant.speech.stt import STTNetworkError, transcribe_audio
from voice_assistant.speech.tts import speak


def run_assistant_step() -> None:
    """Выполняет один шаг ассистента от активации до ответа."""
    drain_speech_queue()

    logger.debug("--- Ожидание активации... ---")
    detector = active_wake_word_detector()

    if detector is not None and detector.name != "fuzzy":
        activation_text = _listen_for_wake_word_streaming(detector)
    else:
        activation_text = _listen_text_or_none(
            timeout_ms=settings.wake_timeout_ms, stage="activation", play_beep=False
        )

    if not activation_text:
        return
    if (detector is None or detector.name == "fuzzy") and not is_wake_word(activation_text):
        return

    speak("Слушаю.")
    intent = _listen_intent_after_activation()
    if intent is None:
        return

    execute_intent(
        intent_name=intent["intent"],
        payload=intent.get("payload"),
        listen=_record_and_transcribe_with_retries,
    )


def _listen_for_wake_word_streaming(detector: Any) -> str | None:
    """Стримит чанки аудио в детектор wake word (Vosk).

    Записывает аудио, параллельно питая детектор чанками. При детекции —
    возвращает распознанное слово (без обращения к Google). При таймауте — None.
    """
    detected: list[str | None] = [None]

    def on_chunk(chunk: Any) -> None:
        word = detector.detect_chunk(chunk)
        if word is not None:
            detected[0] = word

    record_user_speech(timeout_ms=settings.wake_timeout_ms, on_chunk=on_chunk)

    if detected[0] is not None:
        logger.info(f"[wake word детектировано] {detected[0]}")
    return detected[0]


def _listen_intent_after_activation() -> dict[str, Any] | None:
    """Слушает команды после активации, пока не получит валидный интент.

    Лимит попыток: после max_misunderstand непониманий — выход в режим ожидания.
    При таймауте (молчание) — один бип DONE и выход в режим ожидания wake word.
    """
    attempts = 0
    first_attempt = True
    while True:
        command_text = _record_and_transcribe_with_retries(
            stage="command", play_beep=not first_attempt
        )
        first_attempt = False
        if not command_text:
            make_sound(Sound.DONE)
            return None

        intent = parse_voice_intent(command_text)
        if intent:
            return intent

        attempts += 1
        if attempts >= settings.max_misunderstand:
            make_sound(Sound.DONE)
            speak("Не получается. Скажите слово активации снова.")
            return None

        make_sound(Sound.DONE)
        speak("Я вас не поняла, повторите.")


def _listen_text_or_none(timeout_ms: int, stage: str, *, play_beep: bool = True) -> str | None:
    """Слушает микрофон и возвращает распознанный текст.

    Args:
        timeout_ms: Максимум ожидания начала речи.
        stage: Имя стадии для логирования.
        play_beep: Издать бип перед записью (неблокирующе).
    """
    if play_beep:
        make_sound(Sound.READY_TO_LISTEN, block=False)

    audio = record_user_speech(timeout_ms=timeout_ms)
    if audio is None:
        return None

    try:
        text = transcribe_audio(audio)
    except STTNetworkError:
        make_sound(Sound.DONE)
        speak("Нет связи с интернетом.")
        return None

    if text:
        logger.info(f"[распознано:{stage}] {text}")
    return text


def _record_and_transcribe_with_retries(
    stage: str, prompt: str | None = None, *, play_beep: bool = True
) -> str | None:
    """Повторно слушает и распознает речь до успеха или таймаута.

    При таймауте (молчание) — молча возвращает None. Финальный бип DONE —
    ответственность вызывающего уровня (handler или _listen_intent_after_activation).
    При непонимании (речь была, но не распознана) — бип DONE + переспрос.
    """
    while True:
        if prompt:
            speak(prompt)

        text = _listen_text_or_none(
            timeout_ms=settings.command_timeout_ms, stage=stage, play_beep=play_beep
        )
        if text is None:
            return None
        if text:
            return text

        make_sound(Sound.DONE)
        speak("Я вас не поняла, повторите.")
