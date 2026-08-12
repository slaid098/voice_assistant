# 🚀 voice-assistant

![Cover](assets/cover.png)

<!-- tagline-en:start -->
> Voice assistant for the visually impaired — YouTube, weather, timer by voice.
<!-- tagline-en:end -->
<!-- tagline-ru:start -->
> Голосовой ассистент для незрячих — YouTube, погода, таймер голосом.
<!-- tagline-ru:end -->

[English](#-english) | [Русский](#-русский)

---

## 🇺🇸 English

<!-- summary-en:start -->
### ❓ Why
Built for my blind mother. Maximally reliable — no manual steps, no UI, voice-only interaction.

### ✅ What
Voice assistant for visually impaired users. Russian language. Neural wake-word detection (openWakeWord), Google STT + gTTS, YouTube search, weather, timer.
<!-- summary-en:end -->

<!-- features-en:start -->
### Features

| Feature | Description |
|---------|-------------|
| 🎙️ Wake word | Neural wake-word detection via openWakeWord (ONNX, offline). Say 'алекса' to activate. |
| 🔍 YouTube search | Voice query → results announced → navigation (next/back/play). Opens in Vivaldi app-mode. |
| 🌤️ Weather | Current forecast for default city via Open-Meteo (free, no API key). |
| 🕐 Time | Current date and time, announced in natural language. |
| ⏲️ Timer | Voice-activated timer with spoken expiration notification. |
| 🎵 Now playing | Ask 'what's playing?' — announces current video title from browser window. |
| 🔔 Sound cues | Earcons for accessibility: beep before recording, chime on search, fanfare on startup, done after command. |
<!-- features-en:end -->

### Commands
Say the wake word (**алекса**), wait for the beep, then:

| Command | Description |
|---------|-------------|
| **youtube [query]** | Search videos (e.g. 'youtube cats') |
| **weather** | Forecast for default city |
| **time** | Current date and time |
| **timer [N] min/sec/hours** | Set a timer |
| **what's playing** | Announce current video title |
| **help** | List capabilities |

During YouTube search: **next** / **back** / **play** / **stop**.

### Configuration
All settings have defaults — works out of the box. Optional `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `WAKE_WORD` | Wake word | `алекса` |
| `STT_PROVIDER` | Speech recognition: `google` / `vosk` / `auto` | `google` |
| `TTS_PROVIDER` | Text-to-speech: `google` / `vosk` / `auto` | `google` |
| `WEATHER_DEFAULT_CITY` | Default city for weather | `Костюковка` |
| `BROWSER_PATH` | Path to Vivaldi (empty = auto-detect) | (empty) |
| `YOUTUBE_SEARCH_LIMIT` | Search results count | `10` |

### ⚡ Quick Start

1. Download `voice-assistant.zip` from [releases](https://git.slaid098.dev/slaid098/voice_assistant/releases)
2. Unzip to any folder
3. Run `voice-assistant.exe`
4. Optional: double-click `install_autorun.bat` to add to Windows startup

Access at [https://git.slaid098.dev/slaid098/voice_assistant/releases](https://git.slaid098.dev/slaid098/voice_assistant/releases)

---

## 🇷🇺 Русский

<!-- summary-ru:start -->
### ❓ Зачем
Создан для моей мамы. Максимальная надёжность — никаких ручных шагов, без UI, только голос.

### ✅ Что
Голосовой ассистент для незрячих людей. Русский язык. Нейросетевое распознавание слова активации (openWakeWord), Google STT + gTTS, поиск на YouTube, погода, таймер.
<!-- summary-ru:end -->

<!-- features-ru:start -->
### Фичи

| Фича | Описание |
|------|----------|
| 🎙️ Слово активации | Нейросетевое распознавание через openWakeWord (ONNX, офлайн). Скажите 'алекса' для активации. |
| 🔍 Поиск на YouTube | Голосовой запрос → озвучка результатов → навигация (дальше/назад/включить). Открывает в Vivaldi app-режиме. |
| 🌤️ Погода | Текущий прогноз для города по умолчанию через Open-Meteo (бесплатно, без API-ключа). |
| 🕐 Время | Текущие дата и время прописью. |
| ⏲️ Таймер | Голосовой таймер с озвучкой истечения. |
| 🎵 Что играет | Спросите 'что играет?' — назовёт текущее видео из заголовка окна браузера. |
| 🔔 Звуковые ярлыки | Бип перед записью, чайм при поиске, фанфара при старте, финал после команды. |
<!-- features-ru:end -->

### Команды
Скажите слово активации (**алекса**), дождитесь бипа, затем команду:

| Команда | Описание |
|---------|----------|
| **ютуб [запрос]** | Поиск видео (например, «ютуб котики») |
| **погода** | Прогноз для города по умолчанию |
| **время** | Текущие дата и время |
| **таймер [N] мин/сек/часов** | Поставить таймер |
| **название** / **что играет** | Название текущего видео |
| **помощь** | Список возможностей |

Во время поиска YouTube: **дальше** / **назад** / **включить** / **стоп**.

### Конфигурация
Все настройки имеют значения по умолчанию — работает из коробки. Опциональный файл `.env`:

| Переменная | Описание | По умолчанию |
|----------|----------|-------------|
| `WAKE_WORD` | Слово активации | `алекса` |
| `STT_PROVIDER` | Распознавание команд: `google` / `vosk` / `auto` | `google` |
| `TTS_PROVIDER` | Синтез речи: `google` / `vosk` / `auto` | `google` |
| `WEATHER_DEFAULT_CITY` | Город по умолчанию | `Костюковка` |
| `BROWSER_PATH` | Путь к Vivaldi (пусто = авто-detect) | (пусто) |
| `YOUTUBE_SEARCH_LIMIT` | Количество результатов поиска | `10` |

### ⚡ Быстрый старт

1. Скачайте `voice-assistant.zip` со [страницы релизов](https://git.slaid098.dev/slaid098/voice_assistant/releases)
2. Распакуйте в любую папку
3. Запустите `voice-assistant.exe`
4. Опционально: двойной клик `install_autorun.bat` для автозагрузки

Доступ: [https://git.slaid098.dev/slaid098/voice_assistant/releases](https://git.slaid098.dev/slaid098/voice_assistant/releases)

---

## 💬 Support and contacts / Поддержка и контакты

👉 **[slaid098.dev/contacts](https://slaid098.dev/contacts)**
