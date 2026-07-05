import numpy as np


def test_rms_silence():
    """RMS of silence (all zeros) is 0."""
    from voice_assistant.speech.audio import _rms

    samples = np.zeros(1000, dtype=np.int16)
    assert _rms(samples) == 0.0


def test_rms_signal():
    """RMS of a signal is positive."""
    from voice_assistant.speech.audio import _rms

    samples = np.array([100, -100, 200, -200, 50, -50], dtype=np.int16)
    rms = _rms(samples)
    assert rms > 0.0


def test_rms_empty():
    """RMS of empty array is 0."""
    from voice_assistant.speech.audio import _rms

    samples = np.array([], dtype=np.int16)
    assert _rms(samples) == 0.0


def test_is_voice_below_threshold():
    """Silence is not voice."""
    from voice_assistant.speech.audio import _is_voice

    samples = np.zeros(1000, dtype=np.int16)
    assert _is_voice(samples) is False


def test_is_voice_above_threshold():
    """Loud signal is voice."""
    from voice_assistant.speech.audio import _is_voice

    samples = np.array([10000, -10000, 15000, -15000] * 100, dtype=np.int16)
    assert _is_voice(samples) is True


def test_is_voice_constant_dc():
    """Constant DC offset (all same value) should not be detected as voice."""
    from voice_assistant.speech.audio import _is_voice

    samples = np.full(1000, 100, dtype=np.int16)
    # std is 0, so falls to sqrt(mean(x^2)) which is 100 < 200 threshold
    assert _is_voice(samples) is False
