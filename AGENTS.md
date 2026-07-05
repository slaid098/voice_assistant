# AGENTS.md

## Rules
- Save important facts to memory immediately (`memory_save`)
- Search for relevant context before answering (`memory_search`)
- If info is missing — ask, don't guess
- Preserve key decisions and discoveries during compaction

## Project: Voice Assistant

Voice assistant for visually impaired users. Russian language. Google STT + gTTS.

### Architecture
- `src/voice_assistant/` — package (src/ layout)
- `cli.py` — entry point, logging, excepthook, startup sound
- `assistant.py` — orchestrator (thin: wake → listen → intent → execute)
- `config.py` — `Settings` frozen dataclass, `Intent` StrEnum, `IntentRule` dataclass
- `audio/sounds.py` — 4 earcons (mp3) via pygame.mixer, `@with_sound_effects`
- `speech/` — `audio.py` (VAD), `stt.py` (Google), `tts.py` (gTTS + pygame)
- `nlu/` — `wake_word.py` (fuzzy), `intent.py` (fuzzy parser), `handlers.py` (strategy dispatch)
- `services/` — `browser.py`, `commands.py`, `weather.py`, `youtube.py`, `youtube_flow.py`
- `assets/sounds/{1,2,3,4}.mp3` — earcons (packed via importlib.resources)

### Sound triggers
- `Sound.STARTUP` (3) — once at boot
- `Sound.READY_TO_LISTEN` (1) — before each VAD recording + wake word
- `Sound.SEARCH_STARTED` (2) — YouTube query accepted
- `Sound.DONE` (4) — after command execution / error / not understood

### Configuration (.env)
- `WAKE_WORD` — activation word (default: "вики")
- `WAKE_THRESHOLD` — fuzzy match threshold (default: 70)
- `OPENWEATHER_API_KEY` — weather API key
- `WEATHER_DEFAULT_CITY` — default city (default: "Гомель")
- `YOUTUBE_SEARCH_LIMIT` — search results count (default: 10)

### Tech stack
- Python >=3.12, uv, hatchling
- ruff strict (12 rule groups), mypy strict, pytest-cov 75%, xenon
- Pre-commit: ruff + mypy
- CI: lint → typecheck → test (matrix 3.12/3.13/3.14) → complexity
- Release: tag `v*` → Windows PyInstaller → zip with sounds

### Future enhancements (architecture prepared, not implemented)
- Offline STT: Vosk / whisper.cpp / openWakeWord (Protocol: `speech/stt.py`)
- Offline TTS: Silero / RHVoice (Protocol: `speech/tts.py`)
- Keyword spotting: openWakeWord (Protocol: `nlu/wake_word.py`)

### Commands
```bash
uv sync --extra dev          # install
uv run voice-assistant        # run
uv run pytest                 # test
uv run ruff check src/ tests/ # lint
uv run mypy src/              # typecheck
uv run xenon --max-absolute B --max-modules A --max-average A src/  # complexity
```