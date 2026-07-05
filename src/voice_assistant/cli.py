import sys
import threading
import traceback
from datetime import datetime
from types import TracebackType

from loguru import logger

from voice_assistant.assistant import run_assistant_step
from voice_assistant.audio.sounds import Sound, init_sounds, make_sound, speak_with_fallback
from voice_assistant.speech.tts import preload_piper


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    log_file = f"assistant_{datetime.now():%Y-%m-%d}.log"
    logger.add(log_file, level="DEBUG", rotation="10 MB", retention=7, encoding="utf-8")


def _crash_handler(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    """Обрабатывает критические ошибки — озвучивает и завершает работу."""
    logger.critical("Необработанное исключение", exc_info=(exc_type, exc_value, exc_tb))
    print(f"\n{'=' * 60}", file=sys.stderr)
    print("КРИТИЧЕСКАЯ ОШИБКА: Голосовой помощник аварийно завершил работу.", file=sys.stderr)
    print("".join(traceback.format_exception(exc_type, exc_value, exc_tb)), file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)

    try:
        make_sound(Sound.DONE)
        speak_with_fallback("Произошла критическая ошибка. Программа завершит работу.")
    except Exception:
        logger.warning("Не удалось озвучить сообщение о сбое")

    timer = threading.Timer(10.0, lambda: sys.exit(1))
    timer.daemon = True
    timer.start()


def main() -> None:
    setup_logging()
    sys.excepthook = _crash_handler

    init_sounds()
    preload_piper()

    print("=== Голосовой помощник запущен ===")
    make_sound(Sound.STARTUP)

    while True:
        try:
            run_assistant_step()
        except KeyboardInterrupt:
            print("\nЗавершение по Ctrl+C...")
            break
        except Exception as ex:
            tb = traceback.format_exc()
            logger.bind(error=ex, error_type=type(ex).__name__).error(
                f"Ошибка шага ассистента\n{tb}"
            )
            try:
                make_sound(Sound.DONE)
                speak_with_fallback("Произошла ошибка. Повторите команду.")
            except Exception:
                logger.warning("Не удалось озвучить сообщение об ошибке")
