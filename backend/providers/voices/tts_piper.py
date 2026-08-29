# backend\providers\voices\tts_piper.py

import os
import re
import wave
import tempfile
import threading
import logging
from typing import Dict, List, Optional
from PySide6.QtCore import QUrl, QEventLoop
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from backend.services.chat.piper_voice_manager import PiperVoiceManager, DEFAULT_PIPER_VOICE_ID

logger = logging.getLogger("minikick.providers.tts_piper")

class PiperTTSProvider:
    def __init__(self, voice_manager: Optional[PiperVoiceManager] = None):
        self.manager = voice_manager or PiperVoiceManager()
        self.voice_id = DEFAULT_PIPER_VOICE_ID
        self.volume = 1.0
        self.speed_percent = 100
        self.length_scale = 1.0
        self.noise_scale = 0.7
        self.noise_w_scale = 0.35
        self._audio_device_id = "default"
        self._cache: Dict[tuple[str, str], str] = {}
        self._cache_lock = threading.Lock()
        self._loaded_models: Dict[str, any] = {}
        self._models_lock = threading.Lock()
        self._warming_up_voices: set[str] = set()

    def set_synthesis_params(self, length_scale: float = 1.0, noise_scale: float = 0.667, noise_w_scale: float = 0.8) -> None:
        self.length_scale = max(0.2, min(3.0, float(length_scale)))
        self.noise_scale = max(0.0, min(2.0, float(noise_scale)))
        self.noise_w_scale = max(0.0, min(2.0, float(noise_w_scale)))
        self.clear_cache()

    def set_audio_device(self, device_id: str) -> None:
        self._audio_device_id = device_id

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))

    def set_speed(self, speed: float) -> None:
        self.speed_percent = max(50, min(200, int(speed * 100 if speed <= 3.0 else speed)))

    def warm_up(self, voice_id: Optional[str] = None, async_mode: bool = True) -> None:
        target_id = voice_id or self.voice_id or DEFAULT_PIPER_VOICE_ID

        with self._models_lock:
            if target_id in self._loaded_models:
                return
            if target_id in self._warming_up_voices:
                return
            self._warming_up_voices.add(target_id)

        def _do_warm_up():
            try:
                voice = self._get_or_load_voice(target_id)
                if voice is not None:
                    logger.debug("Piper voice '%s' pre-warmed successfully.", target_id)
            except Exception as e:
                logger.debug("Piper warm-up exception for '%s': %s", target_id, e)
            finally:
                with self._models_lock:
                    self._warming_up_voices.discard(target_id)

        if async_mode:
            thread = threading.Thread(target=_do_warm_up, daemon=True, name=f"PiperWarmup_{target_id}")
            thread.start()
        else:
            _do_warm_up()

    @staticmethod
    def _is_speakable_text(text: str) -> bool:
        if not text or not text.strip():
            return False
        cleaned = re.sub(r'https?://\S+|www\.\S+', '', text).strip()
        if not cleaned:
            return False
        return any(c.isalnum() for c in cleaned)

    @staticmethod
    def _prepare_compatible_config(json_path: str) -> str:
        import json
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            
            modified = False
            if "num_symbols" not in cfg:
                phone_map = cfg.get("phoneme_id_map", {})
                if phone_map:
                    all_ids = []
                    for v in phone_map.values():
                        if isinstance(v, list):
                            all_ids.extend(v)
                        elif isinstance(v, int):
                            all_ids.append(v)
                    cfg["num_symbols"] = max(all_ids, default=255) + 1
                else:
                    cfg["num_symbols"] = 256
                modified = True

            if "num_speakers" not in cfg:
                cfg["num_speakers"] = len(cfg.get("speaker_id_map", {})) or 1
                modified = True

            if "audio" not in cfg or "sample_rate" not in cfg["audio"]:
                cfg["audio"] = {"sample_rate": cfg.get("sample_rate", 22050)}
                modified = True

            if "espeak" not in cfg:
                cfg["espeak"] = {"voice": cfg.get("language", {}).get("code", "es")}
                modified = True
            elif "voice" not in cfg["espeak"] or not cfg["espeak"]["voice"]:
                cfg["espeak"]["voice"] = cfg.get("language", {}).get("code", "es")
                modified = True
            else:
                v_str = str(cfg["espeak"]["voice"]).strip()
                if len(v_str) > 8 and ("-" in v_str or "_" in v_str):
                    cfg["espeak"]["voice"] = "es" if "es" in v_str else "es"
                    modified = True

            pt = str(cfg.get("phoneme_type", "espeak")).lower()
            valid_types = {"espeak", "text", "pinyin", "hebrew", "japanese"}
            if pt not in valid_types:
                cfg["phoneme_type"] = "espeak"
                modified = True

            if modified:
                temp_cfg = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                json.dump(cfg, temp_cfg, ensure_ascii=False, indent=2)
                temp_cfg.close()
                return temp_cfg.name
        except Exception as e:
            logger.debug("Config compatibility normalization error for %s: %s", json_path, e)
        return json_path

    def _get_or_load_voice(self, voice_id: str):
        target_voice_id = voice_id or self.voice_id or DEFAULT_PIPER_VOICE_ID
        with self._models_lock:
            if target_voice_id in self._loaded_models:
                return self._loaded_models[target_voice_id]

            if not self.manager.is_voice_installed(target_voice_id):
                installed = self.manager.get_installed_voices()
                if installed:
                    target_voice_id = installed[0]["id"]
                else:
                    logger.warning("No Piper voices installed for voice request: %s", target_voice_id)
                    return None

            onnx_path, json_path = self.manager.get_voice_file_paths(target_voice_id)
            if not os.path.exists(onnx_path) or not os.path.exists(json_path):
                logger.error("Missing files for voice %s: %s, %s", target_voice_id, onnx_path, json_path)
                return None

            try:
                from piper.voice import PiperVoice
                compat_json_path = self._prepare_compatible_config(json_path)
                try:
                    voice = PiperVoice.load(onnx_path, config_path=compat_json_path)
                finally:
                    if compat_json_path != json_path and os.path.exists(compat_json_path):
                        try:
                            os.remove(compat_json_path)
                        except Exception:
                            pass
                self._loaded_models[target_voice_id] = voice
                logger.info("Loaded Piper voice model: %s", target_voice_id)
                return voice
            except Exception as e:
                logger.error("Error loading Piper model %s: %s", target_voice_id, e)
                return None

    def _synthesize_to_file(self, text: str, voice_id: str) -> Optional[str]:
        voice = self._get_or_load_voice(voice_id)
        if not voice:
            return None

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        try:
            from piper.config import SynthesisConfig
            calc_length_scale = max(0.2, min(3.0, self.length_scale * (100.0 / self.speed_percent)))
            syn_config = SynthesisConfig(
                length_scale=calc_length_scale,
                noise_scale=self.noise_scale,
                noise_w_scale=self.noise_w_scale
            )
            with wave.open(temp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(voice.config.sample_rate)
                for chunk in voice.synthesize(text, syn_config=syn_config):
                    wav_file.writeframes(chunk.audio_int16_bytes)
            return temp_path
        except Exception as e:
            logger.error("Synthesis error for text '%s': %s", text[:30], e)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            return None

    def prepare(self, text: str, voice_id: str = None) -> None:
        if not self._is_speakable_text(text):
            return
        target_voice = voice_id or self.voice_id
        cache_key = (text, target_voice)
        with self._cache_lock:
            if cache_key in self._cache:
                return

        temp_path = self._synthesize_to_file(text, target_voice)
        if temp_path:
            with self._cache_lock:
                self._cache[cache_key] = temp_path

    def speak(self, text: str, voice_id: str = None) -> None:
        if not self._is_speakable_text(text):
            return
        target_voice = voice_id or self.voice_id
        cache_key = (text, target_voice)

        temp_path = None
        with self._cache_lock:
            if cache_key in self._cache:
                temp_path = self._cache.pop(cache_key)

        if not temp_path or not os.path.exists(temp_path):
            temp_path = self._synthesize_to_file(text, target_voice)

        if temp_path and os.path.exists(temp_path):
            self._play_audio_file(temp_path)

    def _play_audio_file(self, wav_path: str) -> None:
        player = None
        audio_output = None
        try:
            player = QMediaPlayer()
            audio_output = QAudioOutput()
            try:
                from PySide6.QtMultimedia import QMediaDevices
                target_dev = None
                if hasattr(self, "_audio_device_id") and self._audio_device_id and self._audio_device_id != "default":
                    for dev in QMediaDevices.audioOutputs():
                        dev_id_str = dev.id().data().decode("utf-8", errors="ignore") if hasattr(dev.id(), "data") else str(dev.id())
                        if dev_id_str == self._audio_device_id or dev.description() == self._audio_device_id:
                            target_dev = dev
                            break
                if not target_dev:
                    target_dev = QMediaDevices.defaultAudioOutput()
                if target_dev:
                    audio_output.setDevice(target_dev)
            except Exception as dev_err:
                logger.error("[Piper TTS] Error setting audio output device: %s", dev_err)

            player.setAudioOutput(audio_output)
            audio_output.setVolume(self.volume)
            player.setSource(QUrl.fromLocalFile(os.path.abspath(wav_path)))

            loop = QEventLoop()

            def handle_state(state):
                if state == QMediaPlayer.PlaybackState.StoppedState:
                    loop.quit()

            def handle_status(status):
                if status in (QMediaPlayer.MediaStatus.InvalidMedia, QMediaPlayer.MediaStatus.NoMedia, QMediaPlayer.MediaStatus.EndOfMedia):
                    loop.quit()

            conn_state = player.playbackStateChanged.connect(handle_state)
            conn_status = player.mediaStatusChanged.connect(handle_status)

            player.play()
            loop.exec()

            try:
                player.playbackStateChanged.disconnect(conn_state)
                player.mediaStatusChanged.disconnect(conn_status)
            except Exception:
                pass

        except Exception as e:
            logger.error("[Piper TTS] Playback error: %s", e)
        finally:
            if player:
                try:
                    player.stop()
                    player.setSource(QUrl())
                    player.deleteLater()
                except Exception:
                    pass
            if audio_output:
                try:
                    audio_output.deleteLater()
                except Exception:
                    pass
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    def clear_cache(self) -> None:
        with self._cache_lock:
            for path in self._cache.values():
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            self._cache.clear()

    def stop(self) -> None:
        self.clear_cache()

    def get_available_voices(self) -> List[Dict[str, str]]:
        installed = self.manager.get_installed_voices()
        if not installed:
            catalog = self.manager.get_catalog()
            return [{"id": v["id"], "name": f"{v['name']} (Descargar)"} for v in catalog]
        return [{"id": v["id"], "name": v["name"]} for v in installed]
