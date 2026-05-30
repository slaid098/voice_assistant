import pygame
import pytest
from src.tts import _ensure_mixer


def test_pygame_mixer_init():
    try:
        _ensure_mixer()
        assert pygame.mixer.get_init() is not None
    except pygame.error:
        pytest.skip("No audio device available")
