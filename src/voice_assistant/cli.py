import sys
import traceback
from datetime import datetime

from loguru import logger

from voice_assistant.audio.sounds import Sound, init_sounds, make_sound
from voice_assistant.assistant import run_assistant_step


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    log_file = f"assistant_{datetime.now():%Y-%m-%d}.log"
    logger.add(log_file, level="DEBUG", rotation="10 MB", retention=7, encoding="utf-8")


def _crash_handler(exc_type, exc_value, exc_tb) -> None:
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
    print(f"\n{'=' * 60}", file=sys.stderr)
    print("CRITICAL: Голосовой помощник аварийно завершил работу.", file=sys.stderr)
    print("".join(traceback.format_exception(exc_type, exc_value, exc_tb)), file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)
    input("\nНажмите Enter, чтобы закрыть окно...")


def main() -> None:
    setup_logging()
    sys.excepthook = _crash_handler

    init_sounds()
    make_sound(Sound.STARTUP)

    print("=== Голосовой помощник запущен ===")
    while True:
        try:
            run_assistant_step()
        except KeyboardInterrupt:
            print("\nЗавершение по Ctrl+C...")
            break
        except Exception as ex:
            tb = traceback.format_exc()
            logger.bind(error=ex, error_type=type(ex).__name__).error(f"Ошибка шага ассистента\n{tb}")
            print(f"\n[ОШИБКА] {type(ex).__name__}: {ex}", file=sys.stderr)
            print("Подробности в лог-файле.", file=sys.stderr)