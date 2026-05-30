import numpy as np
from src.audio import _rms


def test_rms_calculation():
    chunk = np.array([100, 200, -100, -200], dtype=np.int16)
    rms = _rms(chunk)
    assert rms > 0
    assert rms < 300


def test_rms_silence():
    chunk = np.zeros(1600, dtype=np.int16)
    rms = _rms(chunk)
    assert rms == 0.0


def test_rms_constant():
    chunk = np.full(1600, 1000, dtype=np.int16)
    rms = _rms(chunk)
    assert 990 < rms < 1010
