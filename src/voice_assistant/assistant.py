from loguru import logger

from voice_assistant.audio.sounds import Sound, make_sound
from voice_assistant.config import settings
from voice_assistant.nlu.handlers import execute_intent
from voice_assistant.nlu.intent import parse_voice_intent
from voice_assistant.nlu.wake_word import is_wake_word
from voice_assistant.services.commands import drain_speech_queue
from voice_assistant.speech.audio import record_user_speech
from voice_assistant.speech.stt import transcribe_audio
from voice_assistant.speech.tts import speak


def run_assistant_step() -> None:
    """Выполняет один шаг ассистента от активации до ответа."""
    drain_speech_queue()

    print("\n--- Ожидание активации... ---")
    activation_text = _listen_text_or_none(
        timeout_ms=settings.wake_timeout_ms, stage="activation"
    )
    if not activation_text:
        return
    if not is_wake_word(activation_text):
        return

    make_sound(Sound.READY_TO_LISTEN)
    speak("Слушаю.")
    intent = _listen_intent_after_activation()
    if intent is None:
        return

    execute_intent(
        intent_name=intent["intent"],
        payload=intent.get("payload"),
        listen=_record_and_transcribe_with_retries,
    )


def _listen_intent_after_activation() -> dict | None:
    """Слушает команды после активации, пока не получит валидный интент."""
    while True:
        command_text = _record_and_transcribe_with_retries(stage="command")
        if not command_text:
            return None

        intent = parse_voice_intent(command_text)
        if intent:
            return intent

        make_sound(Sound.DONE)
        speak("Я вас не поняла, повторите.")


def _listen_text_or_none(timeout_ms: int, stage: str) -> str | None:
    """Слушает микрофон и возвращает распознанный текст."""
    make_sound(Sound.READY_TO_LISTEN)
    audio = record_user_speech(timeout_ms=timeout_ms)
    if audio is None:
        return None

    text = transcribe_audio(audio)
    if text:
        logger.info(f"[recognized:{stage}] {text}")
    return text


def _record_and_transcribe_with_retries(stage: str, prompt: str | None = None) -> str | None:
    """Повторно слушает и распознает речь до успеха или таймаута."""
    while True:
        if prompt:
            speak(prompt)

        text = _listen_text_or_none(timeout_ms=settings.command_timeout_ms, stage=stage)
        if text is None:
            speak("Ушла спать.")
            return None
        if text:
            return text

        make_sound(Sound.DONE)
        speak("Я вас не поняла, повторите.")