"""Тесты экстрактора секции CHANGELOG для release notes.

Покрывает: happy path, тире/дефис в заголовке, секция не найдена, CHANGELOG
отсутствует, пустая секция, срез шапки и trailing self-referential ссылок.
"""

from pathlib import Path

from scripts.release_notes import extract_changelog_section

HAPPY = """# Changelog

Все заметные изменения проекта голосового помощника.

Формат: [Keep a Changelog 1.1.0](https://keepachangelog.com/ru/1.1.0/).

## [0.1.0] — 2026-08-11

### Added
- Голосовой помощник для слабовидящих пользователей. Русский язык.
- Wake word: openWakeWord (нейронный, ONNX, слово «вики»)

[0.1.0]: https://git.slaid098.dev/slaid098/voice_assistant/releases/tag/v0.1.0
"""

HAPPY_DASH = """# Changelog

## [0.1.0] - 2026-08-11

### Fixed
- первый фикс
"""

MULTI = """# Changelog

## [0.2.0] — 2026-09-01

### Changed
- второй релиз

## [0.1.0] — 2026-08-11

### Added
- первый релиз

[0.1.0]: https://git.slaid098.dev/slaid098/voice_assistant/releases/tag/v0.1.0
"""

EMPTY_SECTION = """# Changelog

## [0.1.0] — 2026-08-11
"""

NO_HEADER = """### Added
- без шапки
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "CHANGELOG.md"
    p.write_text(content, encoding="utf-8")
    return p


def test_happy_path_returns_only_bullets(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "v0.1.0")
    assert "### Added" in result
    assert "Голосовой помощник" in result
    assert "Wake word" in result
    assert "## [0.1.0]" not in result
    assert "# Changelog" not in result
    assert "Все заметные изменения" not in result
    assert "Формат:" not in result
    assert "releases/tag/v0.1.0" not in result


def test_em_dash_separator(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "v0.1.0")
    assert "### Added" in result


def test_hyphen_separator(tmp_path: Path):
    p = _write(tmp_path, HAPPY_DASH)
    result = extract_changelog_section(p, "v0.1.0")
    assert "### Fixed" in result
    assert "первый фикс" in result
    assert "## [0.1.0]" not in result


def test_section_not_found_fallback_whole_file(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "v0.2.0")
    assert "# Changelog" in result
    assert "### Added" in result


def test_changelog_missing_returns_empty_string(tmp_path: Path):
    missing = tmp_path / "nope.md"
    assert extract_changelog_section(missing, "v0.1.0") == ""


def test_empty_section_returns_empty(tmp_path: Path):
    p = _write(tmp_path, EMPTY_SECTION)
    result = extract_changelog_section(p, "v0.1.0")
    assert result == ""


def test_strips_header_boilerplate(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "v0.1.0")
    assert "# Changelog" not in result
    assert "Все заметные изменения" not in result
    assert "Keep a Changelog" not in result


def test_strips_trailing_self_referential_links(tmp_path: Path):
    p = _write(tmp_path, MULTI)
    result = extract_changelog_section(p, "v0.1.0")
    assert "### Added" in result
    assert "первый релиз" in result
    assert "## [0.2.0]" not in result
    assert "releases/tag/v0.1.0" not in result


def test_picks_correct_version_in_multisection_changelog(tmp_path: Path):
    p = _write(tmp_path, MULTI)
    result = extract_changelog_section(p, "v0.1.0")
    assert "первый релиз" in result
    assert "второй релиз" not in result


def test_no_trailing_whitespace(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "v0.1.0")
    assert result == result.rstrip()


def test_tag_without_v_prefix(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "0.1.0")
    assert "### Added" in result


def test_tag_not_a_version_fallback_whole_file(tmp_path: Path):
    p = _write(tmp_path, HAPPY)
    result = extract_changelog_section(p, "latest")
    assert "# Changelog" in result
