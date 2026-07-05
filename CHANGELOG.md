# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-07-05

### Added
- Предгенерированные фразы через Google TTS в ассетах (`assets/sounds/phrases/`) — мгновенная озвучка фиксированных фраз без обращения к сети
- `manifest.json` — маппинг текст→MP3-файл для фиксированных фраз
- Dev-скрипт `scripts/gen_phrases.py` для предгенерации фраз через gTTS
- LRU-кэш динамических фраз (только для cloud-провайдера) — повторы летают
- Фраза-признак «Выполняю» перед долгими действиями (погода, YouTube-поиск)
- `TTS_PROVIDER` настройка (`google` | `piper` | `auto`) через `.env`
- Кэширование `is_available()` в Google TTS (DNS-lookup раз в 60с)
- Предзагрузка модели Piper в фоновом потоке при старте
- `.bat`-скрипты для управления автозагрузкой (`install_autorun.bat`, `remove_autorun.bat`)
- Классификация провайдеров: `is_cloud` (cloud кэшируется, local — нет)
- Метод `fixed_phrase()` в TTSProvider Protocol для предгенерированных фраз

### Changed
- Структура ассетов: `assets/sounds/{earcons,phrases,voices/}` — единая папка аудио
- Воспроизведение через `BytesIO` вместо temp-файла на диске
- Убран двойной бип после wake word — только «Слушаю»
- Все настройки VAD вынесены в `.env`: `SILENCE_LIMIT_MS`, `CHUNK_MS`, `VAD_THRESHOLD`, `SAMPLERATE`
- `.env.template` — готовый `.env` с дефолтами и комментариями на русском
- Релизный zip включает `.bat`-скрипты автозагрузки

### Fixed
- Двойной бип после слова активации (бип → «Слушаю» → бип → запись)
- Задержка при озвучке: temp-файл на диске заменён на BytesIO в памяти
- DNS-lookup при каждом `speak()` — теперь кэшируется на 60 секунд
- Молчание при запросе погоды — теперь говорит «Выполняю» перед сетевым запросом

## [1.0.0] — 2026-07-05

### Added
- Sound earcons (4 mp3) from legacy YoutubeVoiceAssistant
- `NOW_PLAYING` intent: "название" / "что играет" / "как называется"
- `get_current_title()` via `win32gui` заголовок окна браузера (Windows)
- Fuzzy wake-word matching (thefuzz + root word)
- Configurable wake word via `.env` (`WAKE_WORD`, `WAKE_ALIASES`)
- Thread-safe timer via `queue.Queue`
- Strategy dispatch for intents (IntentHandler Protocol)
- `src/` layout with subpackages: `audio/`, `speech/`, `nlu/`, `services/`
- `py.typed` marker (PEP 561)
- `.env.template` with all configuration options
- TTS Provider architecture: Google (online) → Piper irina (offline ONNX) fallback
- Accessibility: beep only after wake word, max 3 misunderstandings, crash handler
- Open-Meteo as fallback weather provider (no API key needed)
- CI (lint → typecheck → test → complexity), release workflow (Windows PyInstaller)
- README, LICENSE (MIT), CHANGELOG, AGENTS.md

### Changed
- `Settings` frozen dataclass instead of module-level constants
- `Intent` StrEnum instead of `partial(dict)`
- `IntentRule` typed dataclass instead of `dict`
- `num2words` instead of hardcoded ordinal dictionary
- Removed hardcoded "Костюковка" from weather — city from `.env` (default: Костюковка)
- pygame.mixer for all audio (no pydub/ffmpeg dependency)
- Default city changed to Костюковка

### Removed
- Old flat `src/` layout
- `main.py` (replaced by `cli.py` + `assistant.py`)
- Hardcoded city aliases
