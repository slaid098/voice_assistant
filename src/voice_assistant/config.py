import os
from functools import partial

from dotenv import load_dotenv

load_dotenv()

SAMPLERATE = 16000
CHUNK_MS = 100

WAKE_WORD: str = os.getenv("WAKE_WORD", "вики").strip().lower()
WAKE_THRESHOLD: int = int(os.getenv("WAKE_THRESHOLD", "70"))
WAKE_TIMEOUT_MS: int = int(os.getenv("WAKE_TIMEOUT_MS", "3000"))
COMMAND_TIMEOUT_MS: int = int(os.getenv("COMMAND_TIMEOUT_MS", "6000"))

Intents = partial(
    dict,
    YOUTUBE_SEARCH="youtube_search",
    WEATHER="weather",
    STOP="stop",
    NEXT="next",
    BACK="back",
    SELECT="select",
    PLAY="play",
    TIME="time",
    HELP="help",
    TIMER="timer",
    UNKNOWN="unknown",
)
INTENTS = Intents()

WAKE_ALIASES: list[str] = [
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

JUNK_WORDS: list[str] = [
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
]

INTENT_RULES: list[dict] = [
    {
        "intent": INTENTS["YOUTUBE_SEARCH"],
        "keywords": [
            "ютуб",
            "юту",
            "ютюб",
            "найди на ютубе",
            "включи на ютубе",
            "на ютубе",
            "найди видео",
            "включи видео",
        ],
        "threshold": 60,
        "has_payload": True,
    },
    {
        "intent": INTENTS["WEATHER"],
        "keywords": [
            "погода",
            "погоду",
            "какая погода",
            "прогноз погоды",
            "сколько градусов",
        ],
        "threshold": 60,
        "has_payload": True,
    },
    {
        "intent": INTENTS["TIME"],
        "keywords": [
            "время",
            "который час",
            "сколько времени",
            "подскажи время",
        ],
        "threshold": 65,
        "has_payload": False,
    },
    {
        "intent": INTENTS["TIMER"],
        "keywords": [
            "таймер",
            "поставь таймер",
            "заведи таймер",
        ],
        "threshold": 65,
        "has_payload": True,
    },
    {
        "intent": INTENTS["STOP"],
        "keywords": [
            "стоп",
            "хватит",
            "отмена",
            "остановись",
            "замолчи",
            "пауза",
            "передумал",
        ],
        "threshold": 70,
        "has_payload": False,
    },
    {
        "intent": INTENTS["HELP"],
        "keywords": [
            "помощь",
            "что умеешь",
            "команды",
            "справка",
            "что ты умеешь",
            "какие команды",
            "помоги",
        ],
        "threshold": 65,
        "has_payload": False,
    },
]

CITY: str = "Гомель"
WEATHER_DEFAULT_CITY: str = os.getenv("WEATHER_DEFAULT_CITY", "Костюковка, Гомель").strip()
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "").strip()
YOUTUBE_SEARCH_LIMIT: int = int(os.getenv("YOUTUBE_SEARCH_LIMIT", "10"))