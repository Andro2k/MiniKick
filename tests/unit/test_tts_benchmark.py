# tests\unit\test_tts_benchmark.py

import os
from unittest.mock import MagicMock, patch
from tests.live.tts_benchmark_local import Pyttsx3Engine, PiperEngine, KokoroEngine, LocalTTSBenchmarkRunner

def test_pyttsx3_engine_initialization(monkeypatch):
    mock_pyttsx3 = MagicMock()
    mock_engine = MagicMock()
    mock_pyttsx3.init.return_value = mock_engine
    monkeypatch.setattr("pyttsx3.init", mock_pyttsx3.init)

    engine = Pyttsx3Engine()
    init_time = engine.initialize()
    assert init_time >= 0
    assert engine.name == "pyttsx3 (SAPI5)"

def test_piper_engine_synthesis_mock(monkeypatch, tmp_path):
    engine = PiperEngine(model_name="test_model")
    mock_voice = MagicMock()
    mock_voice.config.sample_rate = 22050
    mock_chunk = MagicMock()
    mock_chunk.audio_int16_bytes = b"\x00\x00" * 1000
    mock_voice.synthesize.return_value = [mock_chunk]
    engine._voice = mock_voice

    sample_out = str(tmp_path / "test_piper.wav")
    res = engine.synthesize("Texto de prueba", sample_out)
    assert res["success"] is True
    assert res["latency_ms"] >= 0
    assert os.path.exists(sample_out)

def test_kokoro_engine_synthesis_mock(monkeypatch, tmp_path):
    import numpy as np
    engine = KokoroEngine(voice_name="em_alex")
    mock_kokoro = MagicMock()
    mock_kokoro.get_voices.return_value = ["em_alex", "af_bella"]
    mock_kokoro.create.return_value = (np.zeros(24000, dtype=np.float32), 24000)
    engine._kokoro = mock_kokoro

    sample_out = str(tmp_path / "test_kokoro.wav")
    res = engine.synthesize("Texto de prueba", sample_out, lang="es")
    assert res["success"] is True
    assert res["latency_ms"] >= 0
    assert os.path.exists(sample_out)

def test_benchmark_runner_setup():
    runner = LocalTTSBenchmarkRunner()
    runner.setup_engines(skip_kokoro=True, skip_piper=True)
    assert len(runner.engines) == 1
    assert runner.engines[0].name == "pyttsx3 (SAPI5)"
