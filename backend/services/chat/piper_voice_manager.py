# backend\services\chat\piper_voice_manager.py

import os
import logging
import urllib.request
from typing import Dict, List, Optional, Tuple, Callable
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("minikick.services.piper_voice_manager")

DEFAULT_PIPER_VOICE_ID = "es_ES-sharvard-medium"

PIPER_VOICE_CATALOG: Dict[str, Dict[str, str]] = {
    "es_ES-sharvard-medium": {
        "id": "es_ES-sharvard-medium",
        "name": "Sharvard (España - Natural • Recomendada)",
        "lang": "es_ES",
        "quality": "medium",
        "size_mb": "41.5 MB",
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json"
    },
    "es_ES-davefx-medium": {
        "id": "es_ES-davefx-medium",
        "name": "DaveFX (España - Claro)",
        "lang": "es_ES",
        "quality": "medium",
        "size_mb": "60.3 MB",
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"
    },
    "es_MX-claude-high": {
        "id": "es_MX-claude-high",
        "name": "Claude (México - Alta Calidad)",
        "lang": "es_MX",
        "quality": "high",
        "size_mb": "115.0 MB",
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json"
    },
    "es_AR-daniela-high": {
        "id": "es_AR-daniela-high",
        "name": "Daniela (Argentina - Alta Calidad)",
        "lang": "es_AR",
        "quality": "high",
        "size_mb": "108.9 MB",
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx.json"
    },
    "es_ES-carlfm-x_low": {
        "id": "es_ES-carlfm-x_low",
        "name": "CarlFM (España - Ultra Ligera)",
        "lang": "es_ES",
        "quality": "x_low",
        "size_mb": "16.8 MB",
        "onnx_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx",
        "json_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx.json"
    }
}

class PiperVoiceManager:
    _instance: Optional['PiperVoiceManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PiperVoiceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._models_dir = self._resolve_models_directory()
        os.makedirs(self._models_dir, exist_ok=True)

    def _resolve_models_directory(self) -> str:
        try:
            from frontend.common.paths import resource_path
            base_dir = resource_path(os.path.join("resources", "models", "piper"))
        except Exception:
            base_dir = os.path.join(os.path.expanduser("~"), ".minikick", "models", "piper")
        
        return os.path.abspath(base_dir)

    @property
    def models_dir(self) -> str:
        return self._models_dir

    def get_catalog(self) -> List[Dict[str, str]]:
        return list(PIPER_VOICE_CATALOG.values())

    def get_voice_metadata(self, voice_id: str) -> Optional[Dict[str, str]]:
        return PIPER_VOICE_CATALOG.get(voice_id)

    def get_voice_file_paths(self, voice_id: str) -> Tuple[str, str]:
        onnx_path = os.path.join(self._models_dir, f"{voice_id}.onnx")
        json_path = os.path.join(self._models_dir, f"{voice_id}.onnx.json")
        return onnx_path, json_path

    def is_voice_installed(self, voice_id: str) -> bool:
        onnx_path, json_path = self.get_voice_file_paths(voice_id)
        if os.path.exists(onnx_path) and os.path.exists(json_path):
            if os.path.getsize(onnx_path) > 1024 and os.path.getsize(json_path) > 10:
                return True
        
        test_cache_onnx = os.path.join(os.getcwd(), "tests", "logs", "tts_models", "piper", f"{voice_id}.onnx")
        test_cache_json = os.path.join(os.getcwd(), "tests", "logs", "tts_models", "piper", f"{voice_id}.onnx.json")
        if os.path.exists(test_cache_onnx) and os.path.exists(test_cache_json):
            try:
                import shutil
                shutil.copy2(test_cache_onnx, onnx_path)
                shutil.copy2(test_cache_json, json_path)
                return True
            except Exception:
                pass
        return False

    def get_installed_voices(self) -> List[Dict[str, str]]:
        installed = []
        for voice_id, meta in PIPER_VOICE_CATALOG.items():
            if self.is_voice_installed(voice_id):
                installed.append({
                    "id": voice_id,
                    "name": meta["name"],
                    "lang": meta["lang"],
                    "quality": meta["quality"]
                })
        return installed

    def download_voice_sync(
        self,
        voice_id: str,
        progress_callback: Optional[Callable[[int, float, float], None]] = None
    ) -> bool:
        meta = self.get_voice_metadata(voice_id)
        if not meta:
            logger.error("Voice ID %s not found in Piper catalog", voice_id)
            return False

        onnx_path, json_path = self.get_voice_file_paths(voice_id)
        os.makedirs(self._models_dir, exist_ok=True)

        try:
            req_json = urllib.request.Request(meta["json_url"], headers={"User-Agent": "MiniKick/1.5"})
            with urllib.request.urlopen(req_json, timeout=15) as resp, open(json_path + ".tmp", "wb") as f:
                f.write(resp.read())
            if os.path.exists(json_path):
                os.remove(json_path)
            os.rename(json_path + ".tmp", json_path)

            req_onnx = urllib.request.Request(meta["onnx_url"], headers={"User-Agent": "MiniKick/1.5"})
            with urllib.request.urlopen(req_onnx, timeout=30) as resp, open(onnx_path + ".tmp", "wb") as f:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                block_size = 1024 * 64
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        down_mb = downloaded / (1024 * 1024)
                        tot_mb = total_size / (1024 * 1024)
                        progress_callback(percent, down_mb, tot_mb)

            if os.path.exists(onnx_path):
                os.remove(onnx_path)
            os.rename(onnx_path + ".tmp", onnx_path)
            logger.info("Successfully downloaded Piper voice %s", voice_id)
            return True
        except Exception as e:
            logger.error("Error downloading Piper voice %s: %s", voice_id, e)
            for tmp in (onnx_path + ".tmp", json_path + ".tmp"):
                if os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
            return False

    def delete_voice(self, voice_id: str) -> bool:
        onnx_path, json_path = self.get_voice_file_paths(voice_id)
        success = True
        for path in (onnx_path, json_path):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.error("Error removing %s: %s", path, e)
                    success = False
        return success


class PiperVoiceDownloadWorker(QThread):
    progress = Signal(str, int, float, float)
    finished = Signal(str, bool, str)

    def __init__(self, voice_id: str, manager: PiperVoiceManager, parent=None):
        super().__init__(parent)
        self.voice_id = voice_id
        self.manager = manager

    def run(self):
        def _on_prog(percent: int, down_mb: float, tot_mb: float):
            if self.isInterruptionRequested():
                raise InterruptedError("Download cancelled by user")
            self.progress.emit(self.voice_id, percent, down_mb, tot_mb)

        try:
            ok = self.manager.download_voice_sync(self.voice_id, progress_callback=_on_prog)
            if ok:
                self.finished.emit(self.voice_id, True, "")
            else:
                self.finished.emit(self.voice_id, False, "Download failed")
        except Exception as e:
            self.finished.emit(self.voice_id, False, str(e))
