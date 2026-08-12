# tests\test_tts_local.py

from backend.providers.voices.tts_local import LocalTTSProvider

def test_local_tts_provider_multiple_speaks():
    provider = LocalTTSProvider(rate=150, initial_volume=0.5)
    voices = provider.get_available_voices()
    assert isinstance(voices, list)
    assert len(voices) > 0
    provider.speak("First test message")
    provider.speak("Second test message")
    provider.speak("Third test message")
