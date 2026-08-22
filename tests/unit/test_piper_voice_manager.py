# tests\unit\test_piper_voice_manager.py

import os
from unittest.mock import MagicMock, patch
from backend.services.chat.piper_voice_manager import PiperVoiceManager, PiperVoiceDownloadWorker, DEFAULT_PIPER_VOICE_ID

def test_piper_voice_manager_catalog():
    manager = PiperVoiceManager()
    catalog = manager.get_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) >= 5
    
    # Check default voice is in catalog
    default_meta = manager.get_voice_metadata(DEFAULT_PIPER_VOICE_ID)
    assert default_meta is not None
    assert default_meta["id"] == DEFAULT_PIPER_VOICE_ID
    assert "onnx_url" in default_meta
    assert "json_url" in default_meta
    
    # Ensure all catalog voices are Spanish
    for voice in catalog:
        assert voice["lang"].startswith("es_"), f"Voice {voice['id']} is not Spanish!"

def test_piper_voice_paths_resolution():
    manager = PiperVoiceManager()
    onnx_p, json_p = manager.get_voice_file_paths("test-voice")
    assert onnx_p.endswith("test-voice.onnx")
    assert json_p.endswith("test-voice.onnx.json")

def test_piper_voice_is_installed_mock(tmp_path):
    manager = PiperVoiceManager()
    manager._models_dir = str(tmp_path)

    assert manager.is_voice_installed("fake_voice") is False

    onnx_file = tmp_path / "fake_voice.onnx"
    json_file = tmp_path / "fake_voice.onnx.json"
    onnx_file.write_bytes(b"\x00" * 2048)
    json_file.write_text('{"key": "value"}')

    assert manager.is_voice_installed("fake_voice") is True
    assert manager.delete_voice("fake_voice") is True
    assert manager.is_voice_installed("fake_voice") is False

def test_piper_voice_download_worker(monkeypatch):
    manager = PiperVoiceManager()
    monkeypatch.setattr(manager, "download_voice_sync", lambda voice_id, progress_callback=None: True)

    worker = PiperVoiceDownloadWorker("es_ES-sharvard-medium", manager)
    results = []
    worker.finished.connect(lambda v_id, ok, msg: results.append((v_id, ok)))
    worker.run()

    assert len(results) == 1
    assert results[0] == ("es_ES-sharvard-medium", True)
