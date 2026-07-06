"""Тесты model_loader — разрешение путей к моделям."""

from pathlib import Path


def test_models_dir_dev_mode(monkeypatch):
    """В dev-режиме models/ в корне проекта (cwd)."""
    from voice_assistant.speech import model_loader

    monkeypatch.delattr(sys_mod(), "frozen", raising=False)
    result = model_loader.models_dir()
    assert result == Path.cwd() / "models"


def test_models_dir_frozen_mode(monkeypatch, tmp_path):
    """В PyInstaller (frozen) models/ рядом с exe."""
    from voice_assistant.speech import model_loader

    fake_exe = tmp_path / "voice-assistant.exe"
    fake_exe.touch()
    monkeypatch.setattr(sys_mod(), "frozen", True, raising=False)
    monkeypatch.setattr(sys_mod(), "executable", str(fake_exe))

    result = model_loader.models_dir()
    assert result == tmp_path / "models"


def test_piper_model_path(monkeypatch):
    """Путь к модели Piper строится из settings.piper_model."""
    from voice_assistant.speech import model_loader

    monkeypatch.setattr(model_loader, "models_dir", lambda: Path("/fake/models"))
    result = model_loader.piper_model_path()
    assert result == Path("/fake/models/piper/ru_RU-irina-medium.onnx")


def test_piper_config_path(monkeypatch):
    """Конфиг Piper — .onnx.json рядом с моделью."""
    from voice_assistant.speech import model_loader

    monkeypatch.setattr(model_loader, "models_dir", lambda: Path("/fake/models"))
    result = model_loader.piper_config_path()
    assert result.name == "ru_RU-irina-medium.onnx.json"


def test_vosk_stt_model_path(monkeypatch):
    from voice_assistant.speech import model_loader

    monkeypatch.setattr(model_loader, "models_dir", lambda: Path("/fake/models"))
    result = model_loader.vosk_stt_model_path()
    assert result == Path("/fake/models/vosk_stt/vosk-model-small-ru-0.22")


def test_vosk_tts_model_path(monkeypatch):
    from voice_assistant.speech import model_loader

    monkeypatch.setattr(model_loader, "models_dir", lambda: Path("/fake/models"))
    result = model_loader.vosk_tts_model_path()
    assert result == Path("/fake/models/vosk_tts/vosk-model-tts-ru-0.7-multi")


def test_ensure_vosk_tts_model_local_exists(monkeypatch, tmp_path):
    """Если модель есть локально — возвращает True."""
    from voice_assistant.speech import model_loader

    model_dir = tmp_path / "vosk_tts" / "vosk-model-tts-ru-0.7-multi"
    model_dir.mkdir(parents=True)
    (model_dir / "model.onnx").touch()

    monkeypatch.setattr(model_loader, "vosk_tts_model_path", lambda: model_dir)
    assert model_loader.ensure_vosk_tts_model() is True


def test_ensure_vosk_tts_model_missing(monkeypatch, tmp_path):
    """Если модели нет локально — возвращает False (авто-скач fallback)."""
    from voice_assistant.speech import model_loader

    monkeypatch.setattr(model_loader, "vosk_tts_model_path", lambda: tmp_path / "nonexistent")
    assert model_loader.ensure_vosk_tts_model() is False


def sys_mod():
    import sys

    return sys
