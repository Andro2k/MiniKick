# tests\unit\test_tts_piper_provider.py

import os
from unittest.mock import MagicMock, patch
from backend.providers.voices.tts_piper import PiperTTSProvider

def test_piper_tts_provider_initialization():
    mock_mgr = MagicMock()
    mock_mgr.get_installed_voices.return_value = [{"id": "es_ES-davefx-medium", "name": "DaveFX (Local)"}]
    
    provider = PiperTTSProvider(voice_manager=mock_mgr)
    assert provider.volume == 1.0
    provider.set_volume(0.6)
    assert provider.volume == 0.6
    provider.set_volume(1.5)
    assert provider.volume == 1.0
    provider.set_volume(-0.5)
    assert provider.volume == 0.0

    voices = provider.get_available_voices()
    assert len(voices) == 1
    assert voices[0]["id"] == "es_ES-davefx-medium"

    # Speed tests
    assert provider.speed_percent == 100
    provider.set_speed(125)
    assert provider.speed_percent == 125
    provider.set_speed(1.25)
    assert provider.speed_percent == 125
    provider.set_speed(30)
    assert provider.speed_percent == 50  # clamped to 50
    provider.set_speed(250)
    assert provider.speed_percent == 200  # clamped to 200

def test_piper_tts_provider_synthesize_mock(tmp_path):
    mock_mgr = MagicMock()
    mock_mgr.is_voice_installed.return_value = True
    mock_mgr.get_voice_file_paths.return_value = (str(tmp_path / "model.onnx"), str(tmp_path / "model.json"))

    provider = PiperTTSProvider(voice_manager=mock_mgr)
    
    mock_voice = MagicMock()
    mock_voice.config.sample_rate = 22050
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = b"\x00\x00" * 500
    mock_voice.synthesize.return_value = [mock_chunk]
    
    provider._loaded_models["es_ES-davefx-medium"] = mock_voice

    sample_out = provider._synthesize_to_file("¡Hola streamer!", "es_ES-davefx-medium")
    assert sample_out is not None
    assert os.path.exists(sample_out)
    
    # Test cleanup
    if os.path.exists(sample_out):
        os.remove(sample_out)

def test_piper_tts_provider_stop():
    provider = PiperTTSProvider()
    provider._cache[("test", "voice")] = "non_existent_file.wav"
    provider.stop()
    assert len(provider._cache) == 0

def test_piper_tts_provider_warm_up():
    mock_mgr = MagicMock()
    mock_mgr.is_voice_installed.return_value = True
    mock_mgr.get_voice_file_paths.return_value = ("fake.onnx", "fake.json")

    provider = PiperTTSProvider(voice_manager=mock_mgr)
    mock_voice = MagicMock()
    mock_voice.synthesize.return_value = [MagicMock()]
    
    with patch.object(provider, "_get_or_load_voice", return_value=mock_voice):
        provider.warm_up("es_ES-sharvard-medium", async_mode=False)
        assert mock_voice.synthesize.called
