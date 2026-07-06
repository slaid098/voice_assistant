import os
from dataclasses import dataclass
from enum import StrEnum

from dotenv import load_dotenv

load_dotenv()


class Intent(StrEnum):
    YOUTUBE_SEARCH = "youtube_search"
    WEATHER = "weather"
    STOP = "stop"
    TIME = "time"
    HELP = "help"
    TIMER = "timer"
    NOW_PLAYING = "now_playing"
    SMALL_TALK = "small_talk"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IntentRule:
    intent: Intent
    keywords: list[str]
    threshold: int
    has_payload: bool


@dataclass(frozen=True)
class Settings:
    wake_word: str
    wake_threshold: int
    wake_timeout_ms: int
    command_timeout_ms: int
    samplerate: int
    chunk_ms: int
    vad_threshold: float
    silence_limit_ms: int
    youtube_search_limit: int
    openweather_api_key: str
    weather_default_city: str
    tts_provider: str
    tts_cache_size: int
    stt_provider: str
    stt_language: str
    wake_word_detector: str
    max_misunderstand: int
    wake_aliases: list[str]
    junk_words: list[str]
    cmd_junk: list[str]
    intent_rules: list[IntentRule]
    piper_model: str
    vosk_stt_model: str
    vosk_tts_model: str
    vosk_tts_speaker: int


def _load_settings() -> Settings:
    wake_aliases_env = os.getenv("WAKE_ALIASES", "")
    wake_aliases = (
        [a.strip().lower() for a in wake_aliases_env.split(",") if a.strip()]
        if wake_aliases_env
        else [
            "вики",
            "wiki",
            "вика",
            "ники",
            "мики",
            "фрики",
            "вику",
            "вике",
            "викки",
        ]
    )

    return Settings(
        wake_word=os.getenv("WAKE_WORD", "вики").strip().lower(),
        wake_threshold=int(os.getenv("WAKE_THRESHOLD", "70")),
        wake_timeout_ms=int(os.getenv("WAKE_TIMEOUT_MS", "30000")),
        command_timeout_ms=int(os.getenv("COMMAND_TIMEOUT_MS", "6000")),
        samplerate=int(os.getenv("SAMPLERATE", "16000")),
        chunk_ms=int(os.getenv("CHUNK_MS", "100")),
        vad_threshold=float(os.getenv("VAD_THRESHOLD", "200.0")),
        silence_limit_ms=int(os.getenv("SILENCE_LIMIT_MS", "1800")),
        youtube_search_limit=int(os.getenv("YOUTUBE_SEARCH_LIMIT", "10")),
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", "").strip(),
        weather_default_city=os.getenv("WEATHER_DEFAULT_CITY", "Костюковка").strip(),
        tts_provider=os.getenv("TTS_PROVIDER", "google").strip().lower(),
        tts_cache_size=int(os.getenv("TTS_CACHE_SIZE", "50")),
        stt_provider=os.getenv("STT_PROVIDER", "google").strip().lower(),
        stt_language=os.getenv("STT_LANGUAGE", "ru-RU").strip(),
        wake_word_detector=os.getenv("WAKE_WORD_DETECTOR", "vosk").strip().lower(),
        max_misunderstand=int(os.getenv("MAX_MISUNDERSTAND", "3")),
        wake_aliases=wake_aliases,
        junk_words=[
            "пожалуйста",
            "про",
            "мне",
            "нам",
            "о",
            "на",
            "подскажи",
            "скажи",
            "привет",
            "слушай",
            "окей",
        ],
        cmd_junk=[
            "какая",
            "какой",
            "какие",
            "какая-то",
            "найди",
            "включи",
            "запусти",
            "покажи",
            "расскажи",
            "в",
            "на",
            "е",
        ],
        intent_rules=[
            IntentRule(
                intent=Intent.YOUTUBE_SEARCH,
                keywords=[
                    "ютуб",
                    "юту",
                    "ютюб",
                    "найди на ютубе",
                    "включи на ютубе",
                    "на ютубе",
                    "найди видео",
                    "включи видео",
                ],
                threshold=60,
                has_payload=True,
            ),
            IntentRule(
                intent=Intent.WEATHER,
                keywords=[
                    "погода",
                    "погоду",
                    "какая погода",
                    "прогноз погоды",
                    "сколько градусов",
                ],
                threshold=65,
                has_payload=True,
            ),
            IntentRule(
                intent=Intent.TIME,
                keywords=[
                    "время",
                    "который час",
                    "сколько времени",
                    "подскажи время",
                ],
                threshold=65,
                has_payload=False,
            ),
            IntentRule(
                intent=Intent.TIMER,
                keywords=[
                    "таймер",
                    "поставь таймер",
                    "заведи таймер",
                ],
                threshold=65,
                has_payload=True,
            ),
            IntentRule(
                intent=Intent.STOP,
                keywords=[
                    "стоп",
                    "хватит",
                    "отмена",
                    "остановись",
                    "замолчи",
                    "пауза",
                    "передумал",
                ],
                threshold=70,
                has_payload=False,
            ),
            IntentRule(
                intent=Intent.HELP,
                keywords=[
                    "помощь",
                    "что умеешь",
                    "команды",
                    "справка",
                    "что ты умеешь",
                    "какие команды",
                    "помоги",
                ],
                threshold=65,
                has_payload=False,
            ),
            IntentRule(
                intent=Intent.NOW_PLAYING,
                keywords=[
                    "название",
                    "что играет",
                    "как называется",
                    "что играет сейчас",
                    "что играет",
                ],
                threshold=65,
                has_payload=False,
            ),
            IntentRule(
                intent=Intent.SMALL_TALK,
                keywords=[
                    "как дела",
                    "как ты",
                    "что нового",
                    "что нового у тебя",
                    "как настроение",
                    "ты тут",
                    "ты здесь",
                ],
                threshold=70,
                has_payload=False,
            ),
        ],
        piper_model=os.getenv("PIPER_MODEL", "ru_RU-irina-medium.onnx").strip(),
        vosk_stt_model=os.getenv("VOSK_STT_MODEL", "vosk-model-small-ru-0.22").strip(),
        vosk_tts_model=os.getenv("VOSK_TTS_MODEL", "vosk-model-tts-ru-0.7-multi").strip(),
        vosk_tts_speaker=int(os.getenv("VOSK_TTS_SPEAKER", "2")),
    )


settings = _load_settings()
