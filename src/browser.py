import webbrowser

from loguru import logger


def open_browser_url(url: str) -> None:
    """The SINGLE public function of this module.

    Opens the default web browser with the provided URL.
    """
    try:
        webbrowser.open(url)
    except Exception as ex:
        logger.bind(error=ex, url=url).error("Не удалось открыть браузер")
