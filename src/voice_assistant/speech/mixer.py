import pygame


class MixerState:
    """Состояние pygame.mixer — инициализирован или нет."""

    def __init__(self) -> None:
        self._initialized = False

    def ensure(self) -> None:
        """Инициализирует pygame mixer один раз."""
        if self._initialized or pygame.mixer.get_init() is not None:
            self._initialized = True
            return
        pygame.mixer.init(frequency=24000, size=-16, channels=1)
        self._initialized = True


_mixer = MixerState()


def ensure_mixer() -> None:
    """Инициализирует pygame mixer один раз."""
    _mixer.ensure()
