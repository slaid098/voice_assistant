import webbrowser

from loguru import logger


def open_browser_url(url: str) -> None:
    """Открывает URL в браузере по умолчанию.

    Args:
        url: Ссылка для открытия.
    """
    try:
        webbrowser.open(url)
    except Exception as ex:
        logger.bind(error=ex, url=url).error("Не удалось открыть браузер")