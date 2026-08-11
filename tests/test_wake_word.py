"""Тесты OpenWakeWordDetector.

Мокаем openwakeword.model.Model — реальную ONNX-модель не загружаем.
Путь alexa_v0.1.onnx существует в установленном пакете openwakeword —
для «модель загрузилась» достаточно замокать только Model. Для «модель
не загрузилась» патчим openwakeword.__file__ на несуществующий путь.
"""

from unittest.mock import MagicMock, patch

import numpy as np


def _make_detector_with_score(score: float):
    """Создаёт OpenWakeWordDetector с замоканной Model.predict.

    predict всегда возвращает {'alexa_v0.1': score}. Путь alexa_v0.1.onnx
    существует в установленном пакете — достаточно замокать только Model.
    """
    fake_model = MagicMock()
    fake_model.predict.return_value = {"alexa_v0.1": score}

    with patch("openwakeword.model.Model", return_value=fake_model):
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()
    return detector


def _make_detector_without_model():
    """Создаёт OpenWakeWordDetector с несуществующим путём модели → _model None.

    Патчит openwakeword.__file__ на несуществующий путь, чтобы alexa_v0.1.onnx
    не нашёлся и __init__ вышел без загрузки модели.
    """
    import openwakeword

    with patch.object(openwakeword, "__file__", "/nonexistent/openwakeword/__init__.py"):
        import voice_assistant.nlu.wake_word as ww_mod

        detector = ww_mod.OpenWakeWordDetector()
    return detector


def test_openwakeword_detect_chunk_positive():
    """score 0.7 (>= 0.5) → detect_chunk возвращает wake_word."""
    detector = _make_detector_with_score(0.7)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) == "алекса"


def test_openwakeword_detect_chunk_negative():
    """score 0.3 (< 0.5) → detect_chunk возвращает None."""
    detector = _make_detector_with_score(0.3)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) is None


def test_openwakeword_detect_chunk_boundary():
    """score ровно 0.5 (>= 0.5) → detect_chunk возвращает wake_word."""
    detector = _make_detector_with_score(0.5)

    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) == "алекса"


def test_openwakeword_is_available_true():
    """Модель загрузилась → is_available() True."""
    detector = _make_detector_with_score(0.0)
    assert detector.is_available() is True


def test_openwakeword_is_available_false():
    """Модель None (не загрузилась) → is_available() False."""
    detector = _make_detector_without_model()
    assert detector.is_available() is False
    chunk = np.zeros(1600, dtype=np.int16)
    assert detector.detect_chunk(chunk) is None


def test_active_detector_openwakeword(monkeypatch):
    """Модель доступна → OpenWakeWordDetector."""
    import voice_assistant.nlu.wake_word as ww_mod

    monkeypatch.setattr(ww_mod.OpenWakeWordDetector, "is_available", lambda self: True)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

    detector = ww_mod.active_wake_word_detector()
    assert detector is not None
    assert detector.name == "openwakeword"


def test_active_detector_unavailable(monkeypatch):
    """Модель не доступна → None."""
    import voice_assistant.nlu.wake_word as ww_mod

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
    fake_model.predict.return_value = {"alexa_v0.1": 0.0}

    with patch("openwakeword.model.Model", return_value=fake_model):
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
    detector = _make_detector_without_model()

    detector.reset()
    assert detector._buf_len == 0
    assert not detector._buffer.any()


def test_active_detector_cached(monkeypatch):
    """active_wake_word_detector возвращает тот же объект при повторном вызове."""
    import voice_assistant.nlu.wake_word as ww_mod

    monkeypatch.setattr(ww_mod.OpenWakeWordDetector, "is_available", lambda self: True)
    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

    first = ww_mod.active_wake_word_detector()
    second = ww_mod.active_wake_word_detector()
    assert first is not None
    assert first is second


def test_active_detector_failure_cached(monkeypatch):
    """После первой неудачи — второй вызов не создаёт новый детектор."""
    import voice_assistant.nlu.wake_word as ww_mod

    monkeypatch.setattr(ww_mod, "_cached_detector", None)
    monkeypatch.setattr(ww_mod, "_load_failed", False)

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


def test_openwakeword_model_real_init() -> None:
    """Integration: реальное создание Model с alexa.

    Alexa — pretrained модель из пакета openwakeword. Ловит API mismatch
    (wakeword_models vs wakeword_model_paths).
    """
    from pathlib import Path

    import openwakeword

    alexa_path = Path(openwakeword.__file__).parent / "resources" / "models" / "alexa_v0.1.onnx"
    if not alexa_path.exists():
        import pytest

        pytest.skip("alexa_v0.1.onnx не найден в пакете openwakeword")

    from openwakeword.model import Model

    model = Model(wakeword_model_paths=[str(alexa_path)])

    chunk = np.zeros(1280, dtype=np.int16)
    scores = model.predict(chunk)
    assert isinstance(scores, dict)
    assert "alexa_v0.1" in scores
