# backend\services\alerts\alert_service.py

import logging
import uuid
import time
from backend.interfaces.alert_interfaces import AlertStorageProtocol
from backend.models.alert_models import AlertEvent, AlertType, AlertConfig
from backend.services.alerts.alert_queue import AlertQueue

logger = logging.getLogger("minikick.services.alerts.service")

class AlertService:
    def __init__(self, storage: AlertStorageProtocol, overlay_server=None, tts_service=None):
        self.storage = storage
        self.overlay_server = overlay_server
        self.tts_service = tts_service
        self.queue = AlertQueue(on_dispatch=self._dispatch_to_overlay)
        self._recent_event_ids: set[str] = set()

    def process_event(self, event: AlertEvent) -> bool:
        if event.event_id in self._recent_event_ids:
            logger.debug("[AlertService] Skipping duplicate event: %s", event.event_id)
            return False

        self._recent_event_ids.add(event.event_id)
        if len(self._recent_event_ids) > 200:
            self._recent_event_ids.pop()

        type_str = event.alert_type.value if isinstance(event.alert_type, AlertType) else str(event.alert_type)
        config = self.storage.get_config(event.platform, type_str)

        if not config.enabled:
            logger.info("[AlertService] Alert %s for %s is disabled in settings.", type_str, event.platform)
            return False

        display_name = event.display_name or event.username
        formatted_text = self._format_template(config.text_template, {
            "user": display_name,
            "username": display_name,
            "platform": event.platform.capitalize(),
            "amount": event.amount,
            "tier": event.tier,
            "message": event.message
        })

        payload = {
            "id": event.event_id,
            "platform": event.platform,
            "alert_type": type_str,
            "username": display_name,
            "formatted_text": formatted_text,
            "message": event.message,
            "amount": event.amount,
            "tier": event.tier,
            "sound_path": config.sound_path,
            "media_path": config.media_path,
            "duration_ms": config.duration_ms,
            "sound_volume": config.sound_volume,
            "tts_read": config.tts_read,
            "timestamp": event.timestamp
        }

        self.queue.enqueue(payload)
        logger.info("[AlertService] Queued %s alert for %s on %s", type_str, display_name, event.platform)
        return True

    def ack_alert(self, alert_id: str | None = None) -> None:
        self.queue.finish_active_alert(alert_id)

    def trigger_test_alert(
        self,
        platform: str = "kick",
        alert_type: str = "follow",
        username: str = "MiniKickStreamer",
        amount: int = 1,
        message: str = "¡Hola a todos!"
    ) -> bool:
        try:
            type_enum = AlertType(alert_type)
        except ValueError:
            type_enum = AlertType.FOLLOW

        event = AlertEvent(
            event_id=f"test_{uuid.uuid4().hex[:8]}",
            platform=platform,
            alert_type=type_enum,
            username=username,
            display_name=username,
            message=message,
            amount=amount,
            tier="1",
            timestamp=time.time()
        )
        return self.process_event(event)

    def get_config(self, platform: str, alert_type: str) -> AlertConfig:
        return self.storage.get_config(platform, alert_type)

    def load_all_configs(self) -> list[AlertConfig]:
        return self.storage.load_all()

    def save_config(self, config: AlertConfig) -> bool:
        return self.storage.save_config(config)

    def save_all(self, configs: list[AlertConfig]) -> bool:
        return self.storage.save_all(configs)

    def _dispatch_to_overlay(self, payload: dict) -> None:
        logger.info("[AlertService] Broadcasting alert to overlay: %s (%s)", payload.get("formatted_text"), payload.get("id"))
        if self.overlay_server:
            try:
                self.overlay_server.trigger_alert(payload)
            except Exception as e:
                logger.error("[AlertService] Error sending alert to overlay server: %s", e)

        if payload.get("tts_read") and self.tts_service:
            try:
                text_to_read = payload.get("formatted_text", "")
                if payload.get("message"):
                    text_to_read += f". {payload['message']}"
                if hasattr(self.tts_service, "speak"):
                    self.tts_service.speak(text_to_read)
                elif hasattr(self.tts_service, "say"):
                    self.tts_service.say(text_to_read)
            except Exception as e:
                logger.error("[AlertService] Error reading alert with TTS: %s", e)

    @staticmethod
    def _format_template(template: str, values: dict) -> str:
        try:
            return template.format(**values)
        except (KeyError, IndexError, ValueError):
            result = template
            for k, v in values.items():
                result = result.replace(f"{{{k}}}", str(v))
            return result
