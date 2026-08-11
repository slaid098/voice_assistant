# Changelog

Все заметные изменения проекта голосового помощника.

Формат: [Keep a Changelog 1.1.0](https://keepachangelog.com/ru/1.1.0/), [Semantic Versioning 2.0.0](https://semver.org/lang/ru/).

## [0.1.0] — 2026-08-11

### Added
- Голосовой помощник для слабовидящих пользователей. Русский язык.
- Wake word: openWakeWord (нейронный, ONNX, слово «вики»)
- STT: Google (cloud) + Vosk (offline) — Protocol, dispatch по STT_PROVIDER
- TTS: Google (cloud) + Vosk TTS (offline, 5 спикеров) — Protocol, dispatch по TTS_PROVIDER
- Команды: погода, YouTube, браузер (Vivaldi app-mode), системные команды
- VAD (RMS threshold), streaming STT
- Звуковые ярлыки (4 earcons) + предгенерированные фразы (Google TTS)
- Текстовая нормализация для TTS (транслитерация EN→RU, clean_title)
- Автозапуск на Windows (Startup folder .lnk)
- PyInstaller сборка через Forgejo Actions (Windows-раннер)

[0.1.0]: https://git.slaid098.dev/slaid098/voice_assistant/releases/tag/v0.1.0
