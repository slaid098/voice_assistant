# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Sound earcons (4 mp3) from legacy YoutubeVoiceAssistant
- `NOW_PLAYING` intent: "название" / "что играет" / "как называется"
- `get_current_title()` via yt-dlp extract_info
- Fuzzy wake-word matching (thefuzz + root word)
- Configurable wake word via `.env` (`WAKE_WORD`)
- Thread-safe timer via `queue.Queue`
- Strategy dispatch for intents (IntentHandler Protocol)
- `src/` layout with subpackages: `audio/`, `speech/`, `nlu/`, `services/`
- `py.typed` marker (PEP 561)
- `.env.template` with all configuration options

### Changed
- `Settings` frozen dataclass instead of module-level constants
- `Intent` StrEnum instead of `partial(dict)`
- `IntentRule` typed dataclass instead of `dict`
- `num2words` instead of hardcoded ordinal dictionary
- Removed hardcoded "Костюковка" from weather — city from `.env`
- pygame.mixer for all audio (no pydub/ffmpeg dependency)

### Removed
- Old flat `src/` layout
- `main.py` (replaced by `cli.py` + `assistant.py`)
- Hardcoded city aliases