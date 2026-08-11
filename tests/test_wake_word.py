"""Тесты OpenWakeWordDetector.

Мокаем openwakeword.model.Model — реальную ONNX-модель не загружаем.
"""

from unittest.mock import MagicMock, patch

import numpy as np


def _make_detector_with_score(score: float):
    """Создаёт OpenWakeWordDetector с замоканной Model.predict.

    predict всегда возвращает {'wiki': score}.
    """
    fake_model = MagicMock()
    fake_model.predict.return_value = {"wiki": score}

    with (
        patch("voice_assistant.nlu.wake_word.resolve_openwakeword_model") as mock_path,
        patch("openwakeword.model.Model", return_value=fake_model),
    ):
        mock_path.return_value.exists.return_value = True
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()
    return detector


def test_openwakeword_detect_chunk_positive():
    """score 0.7 (>= 0.5) → detect_chunk возвращает 'вики'."""
    detector = _make_detector_with_score(0.7)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) == "вики"


def test_openwakeword_detect_chunk_negative():
    """score 0.3 (< 0.5) → detect_chunk возвращает None."""
    detector = _make_detector_with_score(0.3)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) is None


def test_openwakeword_detect_chunk_boundary():
    """score ровно 0.5 (>= 0.5) → detect_chunk возвращает 'вики'."""
    detector = _make_detector_with_score(0.5)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) == "вики"


def test_openwakeword_is_available_true():
    """Модель загрузилась → is_available() True."""
    detector = _make_detector_with_score(0.0)
    assert detector.is_available() is True


def test_openwakeword_is_available_false():
    """Модель None (не загрузилась) → is_available() False."""
    with patch("voice_assistant.nlu.wake_word.resolve_openwakeword_model") as mock_path:
        mock_path.return_value.exists.return_value = False
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()
    assert detector.is_available() is False
    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) is None


def test_active_detector_openwakeword(monkeypatch):
    """wake_word_detector='openwakeword' + модель доступна → OpenWakeWordDetector."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="openwakeword")
    monkeypatch.setattr(ww_mod, "settings", settings)
    monkeypatch.setattr(ww_mod.OpenWakeWordDetector, "is_available", lambda self: True)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

    detector = ww_mod.active_wake_word_detector()
    assert detector is not None
    assert detector.name == "openwakeword"


def test_active_detector_unavailable(monkeypatch):
    """Модель не доступна → None."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="openwakeword")
    monkeypatch.setattr(ww_mod, "settings", settings)
    monkeypatch.setattr(ww_mod.OpenWakeWordDetector, "is_available", lambda self: False)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

    detector = ww_mod.active_wake_word_detector()
    assert detector is None


def test_false_positive_words():
    """«виктория», «актёр», «привет» → None (мок отдаёт score < 0.5)."""
    detector = _make_detector_with_score(0.2)

    chunk = np.zeros(1600, dtype=np.int16)
    for _ in range(3):
        assert detector.detect_chunk(chunk) is None


def test_reset_clears_buffer():
    """reset() очищает буфер и вызывает model.reset()."""
    fake_model = MagicMock()
    fake_model.reset = MagicMock()
    fake_model.predict.return_value = {"wiki": 0.0}

    with (
        patch("voice_assistant.nlu.wake_word.resolve_openwakeword_model") as mock_path,
        patch("openwakeword.model.Model", return_value=fake_model),
    ):
        mock_path.return_value.exists.return_value = True
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()

    chunk = np.zeros(1600, dtype=np.int16)
    detector.detect_chunk(chunk)
    assert detector._buf_len > 0

    detector.reset()
    assert detector._buf_len == 0
    assert not detector._buffer.any()
    fake_model.reset.assert_called_once()


def test_reset_when_model_none():
    """reset() работает безопасно, даже если модель не загрузилась."""
    with patch("voice_assistant.nlu.wake_word.resolve_openwakeword_model") as mock_path:
        mock_path.return_value.exists.return_value = False
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()

    detector.reset()
    assert detector._buf_len == 0
    assert not detector._buffer.any()


def test_active_detector_cached(monkeypatch):
    """active_wake_word_detector возвращает тот же объект при повторном вызове."""
    import dataclasses

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="openwakeword")
    monkeypatch.setattr(ww_mod, "settings", settings)
    monkeypatch.setattr(ww_mod.OpenWakeWordDetector, "is_available", lambda self: True)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

    first = ww_mod.active_wake_word_detector()
    second = ww_mod.active_wake_word_detector()
    assert first is not None
    assert first is second


def test_active_detector_failure_cached(monkeypatch):
    """После первой неудачи — второй вызов не создаёт новый детектор."""
    import dataclasses
    from pathlib import Path

    import voice_assistant.config as config_mod
    import voice_assistant.nlu.wake_word as ww_mod

    settings = dataclasses.replace(config_mod._load_settings(), wake_word_detector="openwakeword")
    monkeypatch.setattr(ww_mod, "settings", settings)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)
    monkeypatch.setattr(
        ww_mod,
        "resolve_openwakeword_model",
        lambda: Path("/nonexistent/wiki.onnx"),
    )

    call_count = 0
    mock_instance = MagicMock()
    mock_instance.is_available.return_value = False

    def fake_constructor():
        nonlocal call_count
        call_count += 1
        return mock_instance

    monkeypatch.setattr(ww_mod, "OpenWakeWordDetector", fake_constructor)

    first = ww_mod.active_wake_word_detector()
    second = ww_mod.active_wake_word_detector()

    assert first is None
    assert second is None
    assert call_count == 1
    assert ww_mod._load_failed is True
