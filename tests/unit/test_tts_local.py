# tests\unit\test_tts_local.py

from unittest.mock import MagicMock
from backend.providers.voices.tts_local import LocalTTSProvider

def test_local_tts_provider_initialization():
    provider = LocalTTSProvider(rate=150, initial_volume=0.5)
    assert provider.rate == 150
    assert provider.volume == 0.5
    voices = provider.get_available_voices()
    assert isinstance(voices, list)

def test_local_tts_provider_volume():
    provider = LocalTTSProvider(rate=150, initial_volume=0.5)
    provider.set_volume(0.8)
    assert provider.volume == 0.8
    provider.set_volume(1.5)
    assert provider.volume == 1.0
    provider.set_volume(-0.5)
    assert provider.volume == 0.0

def test_local_tts_provider_speak(monkeypatch):
    provider = LocalTTSProvider(rate=150, initial_volume=0.5)
    mock_engine = MagicMock()
    monkeypatch.setattr("pyttsx3.init", lambda: mock_engine)
    
    provider.speak("Test voice message")
    mock_engine.setProperty.assert_any_call("rate", 150)
    mock_engine.setProperty.assert_any_call("volume", 0.5)
    mock_engine.say.assert_called_with("Test voice message")
    mock_engine.runAndWait.assert_called_once()
