# AGENTS.md

## Rules
- Save important facts to memory immediately (`memory_save`)
- Search for relevant context before answering (`memory_search`)
- If info is missing — ask, don't guess
- Preserve key decisions and discoveries during compaction

## Project: Voice Assistant

Voice assistant for visually impaired users. Russian language. Google STT + gTTS.
Vosk for local wake-word detection (instant, offline).

### Architecture
- `src/voice_assistant/` — package (src/ layout)
- `cli.py` — entry point, logging, excepthook, startup sound (after full init)
- `assistant.py` — orchestrator (thin: wake → listen → intent → execute)
- `config.py` — `Settings` frozen dataclass, `Intent` StrEnum, `IntentRule` dataclass
- `audio/sounds.py` — 4 earcons (mp3) via pygame.mixer, `@with_sound_effects`
- `speech/` — `audio.py` (VAD + on_chunk streaming), `stt.py` (facade: dispatch by STT_PROVIDER), `tts.py` (gTTS/Piper + pygame), `mixer.py`, `text_normalize.py` (транслитерация EN→RU + clean_title)
  - `providers/stt/` — `base.py` (STTProvider Protocol), `google_stt.py`, `vosk_stt.py`
  - `providers/` — `base.py` (TTSProvider Protocol), `google_tts.py`, `piper_tts.py`
- `nlu/` — `wake_word.py` (WakeWordDetector Protocol + Fuzzy/Vosk detectors), `intent.py` (fuzzy parser), `handlers.py` (strategy dispatch)
- `services/` — `browser.py`, `commands.py`, `weather.py`, `youtube.py`, `youtube_flow.py`
- `assets/sounds/` — единая папка аудио-ассетов:
  - `earcons/{1,2,3,4}.mp3` — звуковые ярлыки (бипы)
  - `phrases/*.mp3` + `manifest.json` — предгенерированные фразы через Google TTS
  - `voices/ru_RU-irina-medium.onnx(.json)` — модель Piper (офлайн TTS, fallback)
- `assets/models/vosk/vosk-model-small-ru-0.22/` — модель Vosk (офлайн STT + wake word, ~45MB)
- `scripts/` — `gen_phrases.py` (предгенерация фраз), `install_autorun.bat` / `remove_autorun.bat` (автозагрузка Windows)

### Sound triggers
- `Sound.STARTUP` (3) — once at boot (after full init: Piper + Vosk loaded, before listening loop)
- `Sound.READY_TO_LISTEN` (1) — before each VAD recording (not on wake word with Vosk)
- `Sound.SEARCH_STARTED` (2) — YouTube query accepted
- `Sound.DONE` (4) — after command execution / error / timeout (single, on top level)

### Text normalization (TTS)
- `speech/text_normalize.py` — `normalize_for_tts(text)` вызывается в `speak()` перед синтезом
- Словарь топ-20 брендов: `YouTube→Ютуб`, `Google→Гугл`, `iPhone→Айфон`...
- `cyrtranslit` для остатка латиницы (фонетическая транслитерация)
- `clean_title(title)` — очистка заголовков от скобок/эмодзи (используется YouTube, browser)

### Configuration (.env)
- `WAKE_WORD` — activation word (default: "вики")
- `WAKE_ALIASES` — comma-separated aliases for fuzzy matching
- `WAKE_THRESHOLD` — fuzzy match threshold (default: 70)
- `WAKE_WORD_DETECTOR` — wake word engine: `vosk` / `fuzzy` (default: `vosk`)
- `STT_PROVIDER` — command recognition: `google` / `vosk` / `auto` (default: `google`)
- `STT_LANGUAGE` — Google STT language (default: `ru-RU`)
- `MAX_MISUNDERSTAND` — max consecutive misunderstandings (default: 3)
- `OPENWEATHER_API_KEY` — weather API key
- `WEATHER_DEFAULT_CITY` — default city (default: "Костюковка")
- `YOUTUBE_SEARCH_LIMIT` — search results count (default: 10)
- `TTS_PROVIDER` — TTS engine: `google` / `piper` / `auto` (default: `google`)
- `TTS_CACHE_SIZE` — LRU cache size for dynamic phrases (default: 50)
- `SILENCE_LIMIT_MS` — silence to end speech (default: 1800)
- `CHUNK_MS` — VAD chunk size (default: 100)
- `VAD_THRESHOLD` — voice detection RMS threshold (default: 200.0)
- `SAMPLERATE` — microphone sample rate (default: 16000)

### Tech stack
- Python >=3.12, uv, hatchling
- ruff strict (12 rule groups), mypy strict, pytest-cov 75%, xenon
- Pre-commit: ruff + mypy
- CI: lint → typecheck → test (matrix 3.12/3.13/3.14) → complexity
- Release: tag `v*` → Windows PyInstaller → zip with sounds + models + .bat

### Implemented providers
- **STT**: Google (cloud, online) + Vosk (local, offline) — STTProvider Protocol, dispatch by STT_PROVIDER
- **TTS**: Google (cloud) + Piper (local) — TTSProvider Protocol, dispatch by TTS_PROVIDER
- **Wake word**: Vosk (local, grammar + fuzzy threshold) + Fuzzy (text, Google path) — WakeWordDetector Protocol
- Auto-fallback: Vosk model not loaded → fuzzy+Google path (user doesn't notice)

### Future enhancements (architecture prepared, not implemented)
- Offline TTS: Silero / RHVoice (Protocol: `speech/tts.py`)
- Keyword spotting: openWakeWord as new WakeWordDetector (Protocol ready in `nlu/wake_word.py`)
- Whisper.cpp as new STTProvider (Protocol ready in `speech/providers/stt/base.py`)

### Commands
```bash
uv sync --extra dev          # install
uv run voice-assistant        # run
uv run pytest                 # test
uv run ruff check src/ tests/ # lint
uv run mypy src/              # typecheck
uv run xenon --max-absolute B --max-modules A --max-average A src/  # complexity
```