"""Экстрактор секции CHANGELOG для release notes.

Вынесен из ``create_release.py`` в отдельный модуль, чтобы импорт функции не
триггерил module-level env-зависимый код ``create_release.py`` (GITHUB_* vars).

Логика:
  1. CHANGELOG отсутствует → "" (не падать).
  2. Версия из тега извлекается regex (v0.1.0 → 0.1.0).
  3. Секция: ``^## [VERSION] [-—] YYYY-MM-DD`` (покрывает дефис и тире).
  4. Контент до следующего ``^## [`` или EOF.
  5. Срез заголовка, шапки (``# Changelog`` и boilerplate) и trailing
     self-referential ссылок ``[...]: https://...``.
  6. Fallback: секция не найдена → весь файл + warning (релиз должен выйти).
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_changelog_section(changelog_path: Path, tag: str) -> str:
    """Извлечь секцию текущей версии из CHANGELOG.md для release notes."""
    if not changelog_path.exists():
        return ""

    text = changelog_path.read_text(encoding="utf-8")

    match = re.search(r"^v?(\d+\.\d+\.\d+)$", tag)
    if not match:
        logger.warning("Tag %r не похож на версию — fallback на весь CHANGELOG", tag)
        return text.strip()
    version = match.group(1)
    escaped = re.escape(version)

    section_match = re.search(
        rf"^## \[{escaped}\]\s*[-—]\s*\d{{4}}-\d{{2}}-\d{{2}}",
        text,
        flags=re.MULTILINE,
    )
    if not section_match:
        logger.warning(
            "Секция версии %s не найдена в %s — fallback на весь CHANGELOG",
            version,
            changelog_path,
        )
        return text.strip()

    next_section = re.search(r"^## \[", text[section_match.end() :], flags=re.MULTILINE)
    end = section_match.end() + next_section.start() if next_section else len(text)
    section = text[section_match.start() : end]

    lines = section.splitlines()
    lines = lines[1:]  # срез заголовка ``## [0.1.0] — дата``

    lines = [
        line
        for line in lines
        if not line.startswith("# Changelog")
        and not line.startswith("Все заметные изменения")
        and not line.startswith("All notable changes")
        and not line.startswith("Формат:")
        and not line.startswith("The format is based on")
        and not re.match(r"^\[.*\]:\s*https://.*$", line)
    ]

    return "\n".join(lines).strip()
