# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] — 2026-07-07

### Fixed
- **Vosk TTS краш на не-кириллических символах.** YouTube-заголовки могут
  содержать китайские иероглифы, подчёркивания, эмодзи-обрывки, которые
  выживали после `clean_title()` и `normalize_for_tts()` и крашили G2P Vosk TTS.
  Добавлена санитизация в `VoskTTSProvider.synthesize()`: только кириллица
  и пунктуация. Применяется только к Vosk TTS — Google и Piper получают
  нормальный текст.
- **Детальное логирование TTS-ошибок.** Теперь лог показывает текст (первые
  80 символов) и ошибку: «TTS vosk упал на тексте: '...'. Ошибка: ...»

## [1.3.1] — 2026-07-07

### Fixed
- **Vosk TTS краш на цифрах.** `normalize_for_tts()` теперь конвертирует все
  цифры в слова через `num2words` (25 → «двадцать пять»). Критично для Vosk TTS
  — его G2P-модуль падал на цифрах. Применяется ко всем провайдерам.
- **«Как дела» → погода.** Добавлен интент `SMALL_TALK` («как дела», «как ты»,
  «что нового»). Порог погоды поднят с 60 до 65 — меньше ложных срабатываний.

## [1.3.0] — 2026-07-06

### Added
- **Vosk TTS провайдер** — новый офлайн TTS через Vosk (ONNX, без torch).
  Модель `vosk-model-tts-ru-0.7-multi` (135 МБ, 5 спикеров). Спикер #2 «irina»
  по умолчанию. `TTS_PROVIDER=vosk` в `.env`. onnxruntime — общий с Piper.
- **Модели в отдельной папке** — `models/{piper,vosk_stt,vosk_tts}/` рядом с exe,
  НЕ внутри. Меньше exe (~50 МБ вместо ~200 МБ). Модели можно обновлять без
  пересборки exe.
- **`speech/model_loader.py`** — централизованное разрешение путей к моделям.
  Настройки `PIPER_MODEL`, `VOSK_STT_MODEL`, `VOSK_TTS_MODEL` в `.env` —
  пользователь может поменять модель без изменения кода.
- **Авто-скачивание Vosk TTS** — если модель отсутствует локально, библиотека
  `vosk_tts` скачивает автоматически в `~/.cache/vosk/`. Аудио-фидбек при
  скачивании: «Загружаю модель голоса...» → «Модель загружена.»
- Настройка `VOSK_TTS_SPEAKER` (0-4, default 2 = Ирина).

### Changed
- **Release ZIP** теперь содержит: `exe` + `models/` + `assets/` + `.env` + `.bat`
- `release.yml` скачивает Vosk TTS модель (135 МБ) при сборке релиза
- `piper_tts.py` и `vosk_stt.py` — пути через `model_loader` вместо
  `importlib.resources`
- `tts.py:_active_providers()` — `vosk` → `[vosk_tts, google_tts, piper_tts]`
- AGENTS.md обновлён

## [1.2.4] — 2026-07-06

### Added
- **Транслитерация английских букв для TTS.** Новый модуль `speech/text_normalize.py`
  с функцией `normalize_for_tts(text)`. Словарь топ-20 брендов (`YouTube→Ютуб`,
  `Google→Гугл`, `iPhone→Айфон`...) + `cyrtranslit` для фонетической транслитерации
  остатка латиницы. Применяется в `speak()` к обоим провайдерам (Google + Piper).
- **Зависимость:** `cyrtranslit>=1.2.0` (25KB, pure Python, MIT).

### Fixed
- **«Точка» во времени.** `_get_time_text()` возвращал `06.07.2026` и `20:15` —
  TTS читал буквально «точка», «двоеточие». Теперь: «Сегодня шестое июля, двадцать
  часов пятнадцать минут» — естественной русской речью через `num2words`.
  Правильное склонение (час/часа/часов, минута/минуты/минут) и женский род
  для минут (одна минута, две минуты).
- **Стартовый бип слишком рано.** `Sound.STARTUP` играл когда Piper ещё грузился
  в фоновом потоке, а Vosk-модель вообще не загружена. Теперь: `preload_piper(wait=True)`
  (блокирует до загрузки) + `preload_wake_word_detector()` (загружает Vosk-модель),
  и только потом бип. Бип = «готова принимать команды».
- **Дублирование `_clean_title`.** Идентичные функции в `youtube.py` и `browser.py`
  → одна `clean_title()` в `text_normalize.py`.

## [1.2.3] — 2026-07-06

### Fixed
- **Убраны лишние бипы при непонимании.** Раньше: бип(DONE) + «не поняла» + бип(READY) + запись.
  Теперь: только «Я вас не поняла, повторите.» → запись. Бипов нет.
- **YouTube-навигация: короткий переспрос.** Раньше при непонимании повторялся полный промпт
  («Видео номер один: Котики. Включить или дальше?»). Теперь: «Не поняла. Включить, дальше
  или назад.» → запись без повтора промпта.
- **Единый счётчик непониманий.** Раньше было два вложенных цикла с «не поняла»
  (пустой текст + несовпадение интента) с раздельными счётчиками. Теперь один цикл,
  один счётчик, 3 попытки на всё.
- **Лимит попыток в `_record_and_transcribe_with_retries`.** Раньше бесконечный цикл
  при пустом тексте (Google не расслышал). Теперь — лимит max_misunderstand.

## [1.2.2] — 2026-07-05

### Fixed
- Vosk CamelCase API: `AcceptWaveform`/`Result`/`PartialResult`/`Reset` (не snake_case)
- Raw PCM вместо WAV-байты в `transcribe()` (Vosk ожидает сырой PCM)
- Проверено локально с реальной моделью vosk-model-small-ru-0.22

## [1.2.0] — 2026-07-05

### Added
- **Vosk офлайн wake-word детектор** — мгновенная реактивность слова активации.
  Мама говорит «Вики» один раз — детектится в стриме аудио, без записи-распознания.
  Больше не нужно повторять 5 раз.
- **STTProvider Protocol** — зеркало TTSProvider: `is_cloud`, `transcribe`, `is_available`.
  Google (cloud) + Vosk (local) провайдеры, dispatch по `STT_PROVIDER`.
- **WakeWordDetector Protocol** — `detect_chunk(audio)` для стриминговых детекторов.
  FuzzyWakeWordDetector (текстовый, Google-путь) + VoskWakeWordDetector (аудио-стрим).
- **Vosk STT** — локальное распознавание команд (модель small-ru-0.22, ~45 МБ).
  Мгновенно, без сети. Dispatch: `STT_PROVIDER=google|vosk|auto`.
- **Двойная защита от ложных срабатываний** Vosk wake-word: грамматика узким
  списком + fuzzy-порог (fuzz.ratio >= WAKE_THRESHOLD).
- **Авто-fallback**: Vosk-модель не загрузилась → авто-откат на fuzzy+Google путь.
- **Streaming аудио**: `record_user_speech(on_chunk=...)` — колбэк для детекторов.
- Настройки: `WAKE_WORD_DETECTOR` (vosk, дефолт), `STT_PROVIDER` (google, дефолт),
  `STT_LANGUAGE`, `MAX_MISUNDERSTAND`.

### Changed
- `speech/stt.py` — тонкий фасад с dispatch (раньше — прямые вызовы Google)
- `nlu/wake_word.py` — Protocol + Fuzzy/Vosk детекторы (раньше — только текст)
- `speech/audio.py` — `print()` → `logger.debug`, убран мёртвый дефолт `timeout_ms=6000`
- `assistant.py` — ветвление wake word по детектору (streaming vs fuzzy)
- `_MAX_MISUNDERSTAND` → `settings.max_misunderstand` (настраиваемый через .env)
- Модель Vosk качается в release workflow (как Piper), упаковывается в exe
- `pyproject.toml` — `vosk` в dependencies, mypy overrides

### Fixed
- Костыль: не было STTProvider Protocol (AGENTS.md врал про «Protocol prepared»)
- Костыль: `STTNetworkError` захардкожен в orchestrator (теперь — в GoogleSTTProvider)
- Костыль: wake_word.py был только текстовый (теперь — Protocol + audio-стрим)
- `AGENTS.md:39` город «Гомель» → «Костюковка» (соответствует config.py)
- `AGENTS.md` «Future enhancements» обновлены: Vosk/openWakeWord — Implemented

## [1.1.1] — 2026-07-05

### Fixed
- Двойной бип DONE при таймауте в YouTube-навигации — DONE играл на двух уровнях
  (внутри listen-функции и в handler). Теперь — единая ответственность: финальный
  бип играет только на верхнем уровне (handler), нижние уровни возвращают None молча.
- STARTUP бип играл до полной готовности — теперь играет после инициализации звуков и
  предзагрузки Piper, прямо перед входом в цикл прослушивания.

### Added
- Интеграционные тесты workflow (`tests/test_workflow.py`) — проверяют точную
  последовательность вызовов make_sound/speak на каждом этапе без реальных аудио/сети:
  - wake → weather (DONE ровно 1)
  - wake → youtube → таймаут навигации (DONE ровно 1, не 2)
  - wake → таймаут команды (DONE ровно 1)
  - wake → 3x непонимание → «Не получается»
  - wake word не распознана → выход без звуков
  - молчание на wake word → выход без звуков

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
