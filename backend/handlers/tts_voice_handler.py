# backend\handlers\tts_voice_handler.py

import logging
from PySide6.QtCore import QObject, Slot

logger = logging.getLogger("minikick.handlers.tts_voice")

class TTSVoiceHandler(QObject):
    _ROLE_PRIORITIES = ("broadcaster", "moderator", "vip", "subscriber")

    def __init__(self, controller, view, service, toast_manager, i18n):
        super().__init__(parent=controller)
        self.controller = controller
        self.view = view
        self.service = service
        self.toast = toast_manager
        self.i18n = i18n

        self._all_voices: list[dict] = []
        self._available_voice_ids: set[str] = set()
        self._voice_worker = None

    def load_voices(self, provider: str, is_initial: bool = False) -> None:
        if self.view is not None:
            loading_str = self.view.i18n.get("chat.status.loading_voices") if hasattr(self.view, "i18n") else "Cargando..."
            self.view.update_voices([("loading", loading_str)], "loading")
        
        cached = self.service.tts._voices_cache.get(provider, [])
        if cached:
            self._on_voices_fetched(cached, provider, is_initial)
            return

        if self._voice_worker:
            if self._voice_worker.isRunning():
                try:
                    self._voice_worker.voices_fetched.disconnect()
                    self._voice_worker.error_occurred.disconnect()
                except Exception:
                    pass
                self._voice_worker.requestInterruption()
                self._voice_worker.wait(300)
            self._voice_worker.deleteLater()
            self._voice_worker = None

        from backend.workers import VoiceFetcherWorker
        self._voice_worker = VoiceFetcherWorker(self.service.tts, provider, parent=self)
        self._voice_worker.voices_fetched.connect(
            lambda voices, prov: self._on_voices_fetched(voices, prov, is_initial)
        )
        self._voice_worker.error_occurred.connect(self._on_voices_error)
        self._voice_worker.start()

    @Slot(object, str, bool)
    def _on_voices_fetched(self, voices: list, provider: str, is_initial: bool) -> None:
        self._all_voices = voices
        self._available_voice_ids = {v["id"] for v in voices}
        saved_voice_id = self.service.get_saved_voice_id(provider)

        if provider in ("local", "piper"):
            langs = [provider.capitalize()]
            sel_prefix = provider.capitalize()
        else:
            langs = list(dict.fromkeys(
                "-".join(v["id"].split("-")[:2]) if "-" in v["id"] else "Web Voice"
                for v in self._all_voices
            ))
            sel_prefix = "-".join(saved_voice_id.split("-")[:2]) if ("-" in saved_voice_id and saved_voice_id) else (langs[0] if langs else "")

        if self.view is not None:
            self.view.update_languages(langs, sel_prefix)
            self.filter_voices_by_language(sel_prefix, select_id=saved_voice_id, play_test=(not is_initial))

        if self._voice_worker:
            self._voice_worker.deleteLater()
            self._voice_worker = None

    @Slot(str, str)
    def _on_voices_error(self, error_msg: str, provider: str) -> None:
        if provider == "piper":
            fallback = [{"id": "es_ES-sharvard-medium", "name": "Sharvard (Local)"}]
        elif provider == "web":
            fallback = [
                {"id": "es-ES-AlvaroNeural", "name": "Álvaro (Sin conexión)"},
                {"id": "es-MX-JorgeNeural", "name": "Jorge (Sin conexión)"}
            ]
        else:
            fallback = [{"id": "default", "name": "SAPI5 Voice"}]

        self._on_voices_fetched(fallback, provider, is_initial=True)
        
        if self.toast:
            self.toast.show_toast(
                title=self.i18n.get("chat.status.tts_error_title"),
                message=self.i18n.get("chat.status.tts_error_offline").replace("{error}", error_msg),
                state="warning"
            )

    @Slot(str)
    def filter_voices_by_language(self, lang_prefix: str = "", select_id: str = None, play_test: bool = False) -> None:
        provider = self.view.tts_provider if hasattr(self.view, "tts_provider") else ("web" if self.view.is_web_provider else "piper")
        filtered = [(v["id"], v["name"]) for v in self._all_voices]
            
        final_select_id = select_id
        if filtered:
            available_ids = [v[0] for v in filtered]
            if not final_select_id or final_select_id not in available_ids:
                final_select_id = filtered[0][0]
                
        if final_select_id and final_select_id != self.service.get_saved_voice_id(provider):
            self.service.set_voice(provider, final_select_id)
            self.controller.sync_settings_cache()

        settings = self.service.get_settings()
        role_voices = {
            "broadcaster": settings.get("role_voice_broadcaster", ""),
            "moderator": settings.get("role_voice_moderator", ""),
            "vip": settings.get("role_voice_vip", ""),
            "subscriber": settings.get("role_voice_subscriber", "")
        }

        all_voices_list = []
        for v in self._all_voices:
            v_id = v["id"]
            v_name = v["name"]
            if "-" in v_id and provider == "web":
                region = "-".join(v_id.split("-")[:2])
                display_name = f"[{region}] {v_name}"
            elif provider == "piper":
                display_name = f"[Piper] {v_name}"
            else:
                display_name = f"[Local] {v_name}"
            all_voices_list.append((v_id, display_name))
            
        if self.view is not None:
            self.view.update_voices(filtered, final_select_id, role_voices, all_voices_list)

    def handle_voice_change(self, voice_id: str) -> None:
        provider = self.view.tts_provider if hasattr(self.view, "tts_provider") else ("web" if self.view.is_web_provider else "piper")
        logger.info("[User Action] Selected TTS voice: voice_id='%s', provider='%s'", voice_id, provider)
        self.service.set_voice(provider, voice_id)
        self.controller.sync_settings_cache()

    def handle_provider_change(self, provider_val) -> None:
        if isinstance(provider_val, str):
            provider = provider_val
        elif isinstance(provider_val, bool):
            provider = "web" if provider_val else "piper"
        else:
            provider = "piper"

        logger.info("[User Action] Changed TTS engine provider to: '%s'", provider)
        self.service.set_provider(provider)
        self.controller.sync_settings_cache()
        self.load_voices(provider)
        
        if self.toast:
            if provider == "piper":
                mode_name = self.i18n.get("chat.status.provider_piper")
                state_color = "success"
            elif provider == "web":
                mode_name = self.i18n.get("chat.status.provider_cloud")
                state_color = "info"
            else:
                mode_name = self.i18n.get("chat.status.provider_local")
                state_color = "warning"

            self.toast.show_toast(
                title=self.view.i18n.get("chat.status.provider_title"),
                message=self.i18n.get("chat.status.provider_active").replace("{mode}", mode_name),
                state=state_color
            )

    def open_piper_voices_dialog(self) -> None:
        from frontend.dialogs import PiperVoicesDialog
        dialog = PiperVoicesDialog(self.i18n, self.service, parent=self.controller.view if hasattr(self.controller, "view") else None)
        dialog.voices_updated.connect(lambda: self.load_voices("piper"))
        dialog.exec()

    def handle_voice_test(self, voice_id: str) -> None:
        if voice_id:
            logger.info("[User Action] Testing TTS sample voice: voice_id='%s'", voice_id)
            sample_text = self.i18n.get("chat.status.voice_test_sample")
            self.service.speak(sample_text, voice_id=voice_id)

    def is_role_enabled(self, badges: list, settings: dict) -> bool:
        for badge in self._ROLE_PRIORITIES:
            if badge in badges:
                return settings.get(f"role_enabled_{badge}", True)
        return settings.get("role_enabled_everyone", True)

    def resolve_voice_for_badges(self, badges: list, settings: dict) -> str | None:
        for badge in self._ROLE_PRIORITIES:
            if badge in badges:
                return settings.get(f"role_voice_{badge}") or None
        return None
