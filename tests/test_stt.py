from unittest.mock import patch
import numpy as np
from src.stt import transcribe_audio


@patch("speech_recognition.Recognizer.recognize_google", return_value="привет вики")
def test_transcribe_audio(mock_recognize):
    audio_data = np.zeros(16000, dtype=np.int16)
    text = transcribe_audio(audio_data)
    assert text == "привет вики"
