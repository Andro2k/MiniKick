# resources\tests\test_audio_acoustic_and_anti_spam.py

import array
import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from backend.providers.voices.piper_provider import PiperTTSProvider
from backend.handlers.spam_handler import ChatFilterHandler
from backend.services.chat.chat_pipeline import ChatMessageDTO


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app

def test_piper_peak_normalization_boosts_low_amplitude():
    raw_samples = array.array('h', [0, 1000, -2500, 5000, -4000, 100])
    pcm_bytes = raw_samples.tobytes()

    normalized = PiperTTSProvider._normalize_peak_pcm(pcm_bytes, target_peak=31500, max_gain=3.0)
    norm_samples = array.array('h')
    norm_samples.frombytes(normalized)

    assert max(abs(s) for s in norm_samples) == 15000
    assert norm_samples[3] == 15000
    assert norm_samples[2] == -7500

def test_piper_peak_normalization_scales_cleanly_to_target():
    raw_samples = array.array('h', [0, 5000, -15750, 10000])
    pcm_bytes = raw_samples.tobytes()

    normalized = PiperTTSProvider._normalize_peak_pcm(pcm_bytes, target_peak=31500, max_gain=3.0)
    norm_samples = array.array('h')
    norm_samples.frombytes(normalized)

    assert max(abs(s) for s in norm_samples) == 31500
    assert norm_samples[2] == -31500

def test_piper_peak_normalization_leaves_near_peak_untouched():
    raw_samples = array.array('h', [0, 31600, -32000])
    pcm_bytes = raw_samples.tobytes()

    normalized = PiperTTSProvider._normalize_peak_pcm(pcm_bytes, target_peak=31500)
    assert normalized == pcm_bytes

def test_piper_peak_normalization_empty_or_silence():
    assert PiperTTSProvider._normalize_peak_pcm(b"") == b""
    silent = array.array('h', [0, 0, 0, 0]).tobytes()
    assert PiperTTSProvider._normalize_peak_pcm(silent) == silent

def test_piper_instant_stop_terminates_player_and_loop():
    provider = PiperTTSProvider()
    mock_player = MagicMock()
    mock_loop = MagicMock()
    mock_loop.isRunning.return_value = True

    provider._current_player = mock_player
    provider._current_loop = mock_loop

    provider.stop()

    mock_player.stop.assert_called_once()
    mock_loop.quit.assert_called_once()

def test_music_cubic_perceptual_volume():
    from backend.providers.music.youtube_provider import YouTubeMusicProvider

    prov = YouTubeMusicProvider.__new__(YouTubeMusicProvider)
    prov._volume_gain = 0.10
    prov._is_ducked = False
    prov._duck_factor = 0.30
    prov.loudness_normalization_enabled = False
    prov.current_song = None

    eff_10 = prov._calculate_effective_volume()
    assert pytest.approx(eff_10, abs=1e-5) == 0.001

    prov._volume_gain = 0.50
    eff_50 = prov._calculate_effective_volume()
    assert pytest.approx(eff_50, abs=1e-5) == 0.125

    prov._volume_gain = 1.00
    eff_100 = prov._calculate_effective_volume()
    assert pytest.approx(eff_100, abs=1e-5) == 1.0

def test_music_ducking_attenuates_volume():
    from backend.providers.music.youtube_provider import YouTubeMusicProvider

    prov = YouTubeMusicProvider.__new__(YouTubeMusicProvider)
    prov._volume_gain = 0.50
    prov._is_ducked = False
    prov._duck_factor = 0.30
    prov.loudness_normalization_enabled = False
    prov.current_song = None
    prov.audio_output = MagicMock()

    base_eff = prov._calculate_effective_volume()
    assert pytest.approx(base_eff, abs=1e-5) == 0.125

    prov.set_ducking(True)
    assert prov._is_ducked is True
    ducked_eff = prov._calculate_effective_volume()
    assert pytest.approx(ducked_eff, abs=1e-5) == 0.125 * 0.30
    prov.audio_output.setVolume.assert_called_with(pytest.approx(ducked_eff, abs=1e-5))

    prov.set_ducking(False)
    assert prov._is_ducked is False
    assert pytest.approx(prov._calculate_effective_volume(), abs=1e-5) == 0.125

def test_clean_message_for_tts_anti_spam_collapse():
    handler = ChatFilterHandler(i18n=None, service=None)

    text = "holaaaaaaaaa amigo 77777777777 !!!!!!!!"
    cleaned = handler.clean_message_for_tts(text)
    assert "holaaa" in cleaned
    assert "holaaaaa" not in cleaned
    assert "777" in cleaned
    assert "7777" not in cleaned
    assert "!!!" in cleaned

    repeat_words = "ja ja ja ja ja ja ja que gracioso"
    cleaned_words = handler.clean_message_for_tts(repeat_words)
    assert "ja ja que gracioso" in cleaned_words

def test_clean_message_for_tts_anti_spam_max_length_clamp():
    handler = ChatFilterHandler(i18n=None, service=None)

    huge_text = " ".join(f"palabra_{i}" for i in range(50))
    cleaned = handler.clean_message_for_tts(huge_text)
    assert len(cleaned) <= handler.MAX_TTS_TEXT_LENGTH + 3
    assert cleaned.endswith("...")

def test_chat_controller_skiptts_command(qapp):
    from backend.controllers.chat_controller import ChatController

    mock_view = MagicMock()
    mock_service = MagicMock()
    mock_command_service = MagicMock()
    mock_spam_service = MagicMock()
    mock_i18n = MagicMock()
    mock_i18n.get.side_effect = lambda key: f"translated_{key}"
    mock_toast = MagicMock()

    controller = ChatController(
        view=mock_view,
        service=mock_service,
        command_service=mock_command_service,
        spam_service=mock_spam_service,
        i18n=mock_i18n,
        toast_manager=mock_toast
    )

    dto = ChatMessageDTO(
        user="ModUser",
        content="!skiptts",
        badges=["moderator"],
        color="#FFF",
        msg_id="123",
        sender_id=1,
        timestamp="12:00:00",
        platform="kick",
        is_command=True
    )

    controller._handle_plugin_skiptts(dto)

    mock_service.stop_tts.assert_called_once()
    mock_command_service.send_response.assert_called_once()
    mock_toast.show_toast.assert_called_once()
