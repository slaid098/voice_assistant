"""Тесты нормализации текста для TTS."""

from voice_assistant.speech.text_normalize import clean_title, normalize_for_tts


class TestNormalizeForTts:
    def test_pure_russian_unchanged(self):
        assert normalize_for_tts("Привет, как дела?") == "Привет, как дела?"

    def test_empty_string(self):
        assert normalize_for_tts("") == ""

    def test_brand_youtube(self):
        assert "ютуб" in normalize_for_tts("Смотрите YouTube канал")

    def test_brand_google(self):
        assert "гугл" in normalize_for_tts("Поиск в Google")

    def test_brand_iphone(self):
        assert "айфон" in normalize_for_tts("Новый iPhone")

    def test_brand_case_insensitive(self):
        result = normalize_for_tts("YOUTUBE и Youtube")
        assert result.count("ютуб") == 2

    def test_brand_whole_phrase(self):
        assert normalize_for_tts("YouTube Music") == "ютуб мьюзик"

    def test_translit_english_word(self):
        result = normalize_for_tts("Eminem")
        assert result == "Еминем"

    def test_translit_mixed_text(self):
        result = normalize_for_tts("Смотрите Eminem на YouTube")
        assert "Еминем" in result
        assert "ютуб" in result
        assert "Смотрите" in result
        assert "на" in result

    def test_translit_preserves_punctuation(self):
        result = normalize_for_tts("Hello, World!")
        assert "," in result
        assert "!" in result

    def test_no_latin_no_change(self):
        text = "Шестое июля, двадцать часов"
        assert normalize_for_tts(text) == text

    def test_digits_preserved(self):
        result = normalize_for_tts("Видео 123")
        assert "123" in result

    def test_mixed_case_brand(self):
        assert "ютуб" in normalize_for_tts("Открой YouTube")
        assert "ютуб" in normalize_for_tts("Открой youtube")
        assert "ютуб" in normalize_for_tts("Открой YouTuBe")


class TestCleanTitle:
    def test_strips_brackets(self):
        assert clean_title("Hello [Official]") == "Hello"

    def test_strips_parens(self):
        assert clean_title("Song (feat. X)") == "Song"

    def test_strips_curly_braces(self):
        assert clean_title("Test {music}") == "Test"

    def test_strips_emoji(self):
        assert clean_title("Emoji 🎵 Test") == "Emoji Test"

    def test_collapses_spaces(self):
        assert clean_title("  spaces  ") == "spaces"

    def test_keeps_latin_for_translit(self):
        result = clean_title("Eminem - Lose Yourself")
        assert "Eminem" in result

    def test_keeps_cyrillic(self):
        assert clean_title("Котики играют") == "Котики играют"

    def test_empty(self):
        assert clean_title("") == ""
