# Changelog

Все заметные изменения проекта голосового помощника.

Формат: [Keep a Changelog 1.1.0](https://keepachangelog.com/ru/1.1.0/), [Semantic Versioning 2.0.0](https://semver.org/lang/ru/).

## [Unreleased]

### Changed
- Wake word: «вики» заменён на «алекса» (PR #20)
- `WAKE_TIMEOUT_MS` переименован в `WAKE_CACHE_RESET_MS` — сброс состояния детектора wake word каждые N мс тишины (PR #21)
- HELP сокращён: «Вот что я умею: ютуб, погода, время, таймер, название видео.» (PR #21)
- Погода всегда использует город по умолчанию (`WEATHER_DEFAULT_CITY`), игнорирует город из голосовой команды (PR #21)
- README стандартизирован: bilingual EN/RU, 12 delimiter tags, cover.png, ссылки на Forgejo (PR #23)
- `pyproject.toml`: ruff `target-version="py313"`, mypy `python_version="3.13"` — соответствие `requires-python>=3.13` (PR #23)
- Cover.png перегенерирован: один микрофон (alone mode, 480×480), title lowercase (PR #24, #26)

### Removed
- SMALL_TALK intent — «как дела» теперь → UNKNOWN → «Я не знаю такую команду» (PR #21)
- OpenWeather API полностью удалён — остался только Open-Meteo (без API key) (PR #23)
- Поле `openweather_api_key` удалено из Settings и `.env.template` (PR #23)
- Поле `wake_word_detector` удалено из Settings — только openwakeword, не настраивается (PR #20)

### Fixed
- Release notes на Forgejo теперь содержат только секцию текущей версии из CHANGELOG (без шапки, self-referential ссылки, boilerplate) — PR #27
- Параметр openwakeword `wakeword_model_paths` (не `wakeword_models`) — критический баг загрузки модели (PR #19)
- PyInstaller `--collect-all sklearn` (не `scikit-learn`) — IMPORT name, не PyPI name (PR #16)
- `--onedir` вместо `--onefile` — убрано 341MB temp unpack (PR #19)

## [0.1.0] — 2026-08-11

### Added
- Голосовой помощник для слабовидящих пользователей. Русский язык.
- Wake word: openWakeWord (нейронный, ONNX, слово «алекса»)
- STT: Google (cloud) + Vosk (offline) — Protocol, dispatch по STT_PROVIDER
- TTS: Google (cloud) + Vosk TTS (offline, 5 спикеров) — Protocol, dispatch по TTS_PROVIDER
- Команды: погода, YouTube, браузер (Vivaldi app-mode), системные команды
- VAD (RMS threshold), streaming STT
- Звуковые ярлыки (4 earcons) + предгенерированные фразы (Google TTS)
- Текстовая нормализация для TTS (транслитерация EN→RU, clean_title)
- Автозапуск на Windows (Startup folder .lnk)
- PyInstaller сборка через Forgejo Actions (Windows-раннер)

[Unreleased]: https://git.slaid098.dev/slaid098/voice_assistant/compare/v0.1.0...HEAD
[0.1.0]: https://git.slaid098.dev/slaid098/voice_assistant/releases/tag/v0.1.0
