# backend\database\alert_storage.py

import logging
from .database_manager import DatabaseManager
from backend.models import AlertConfig, AlertType

logger = logging.getLogger("minikick.database.alert_storage")

DEFAULT_TEMPLATES = {
    AlertType.FOLLOW.value: "¡{user} te acaba de seguir!",
    AlertType.SUBSCRIPTION.value: "¡{user} se ha suscrito (Tier {tier})!",
    AlertType.RESUB.value: "¡{user} renovó su suscripción por {amount} meses!",
    AlertType.SUB_GIFT.value: "¡{user} regaló {amount} suscripciones!",
    AlertType.RAID.value: "¡{user} llegó con una raid de {amount} espectadores!",
    AlertType.CHEER.value: "¡{user} envió {amount} bits!"
}

class SQLiteAlertStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._cache: dict[tuple[str, str], AlertConfig] = {}
        self._is_loaded = False

    def load_all(self) -> dict[tuple[str, str], AlertConfig]:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT platform, alert_type, enabled, sound_path, media_path,
                           text_template, duration_ms, sound_volume, tts_read,
                           layout, style, text_color, highlight_color, font_family,
                           font_size, text_align
                    FROM alert_configs
                """)
                rows = cursor.fetchall()
                configs = {}
                for row in rows:
                    cfg = AlertConfig(
                        platform=str(row[0]),
                        alert_type=str(row[1]),
                        enabled=bool(row[2]),
                        sound_path=str(row[3] or ""),
                        media_path=str(row[4] or ""),
                        text_template=str(row[5] or "{user}"),
                        duration_ms=int(row[6] or 5000),
                        sound_volume=float(row[7] if row[7] is not None else 0.8),
                        tts_read=bool(row[8]),
                        layout=str(row[9] or "above"),
                        style=str(row[10] or "compact"),
                        text_color=str(row[11] or "#FFFFFF"),
                        highlight_color=str(row[12] or ""),
                        font_family=str(row[13] or "Outfit"),
                        font_size=int(row[14] or 24),
                        text_align=str(row[15] or "center")
                    )
                    configs[(cfg.platform, cfg.alert_type)] = cfg

                self._cache = configs
                self._is_loaded = True
                return dict(self._cache)
        except Exception as e:
            logger.error("[AlertStorage] Error loading all alert configs: %s", e)
            return dict(self._cache)

    def get_config(self, platform: str, alert_type: str) -> AlertConfig:
        key = (platform.lower(), alert_type.lower())
        if not self._is_loaded:
            self.load_all()

        if key in self._cache:
            return self._cache[key]

        template = DEFAULT_TEMPLATES.get(alert_type.lower(), "¡{user} en {platform}!")
        default_cfg = AlertConfig(
            platform=platform.lower(),
            alert_type=alert_type.lower(),
            enabled=True,
            sound_path="",
            media_path="",
            text_template=template,
            duration_ms=5000,
            sound_volume=0.8,
            tts_read=False,
            layout="above",
            style="compact",
            text_color="#FFFFFF",
            highlight_color="",
            font_family="Outfit",
            font_size=24,
            text_align="center"
        )
        self._cache[key] = default_cfg
        return default_cfg

    def save_config(self, config: AlertConfig) -> bool:
        return self.save_all([config])

    def save_all(self, configs: list[AlertConfig]) -> bool:
        if not configs:
            return True
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                data = [
                    (
                        c.platform.lower(),
                        c.alert_type.lower(),
                        1 if c.enabled else 0,
                        c.sound_path,
                        c.media_path,
                        c.text_template,
                        c.duration_ms,
                        c.sound_volume,
                        1 if c.tts_read else 0,
                        c.layout,
                        c.style,
                        c.text_color,
                        c.highlight_color,
                        c.font_family,
                        c.font_size,
                        c.text_align
                    )
                    for c in configs
                ]
                cursor.executemany("""
                    INSERT INTO alert_configs (
                        platform, alert_type, enabled, sound_path, media_path,
                        text_template, duration_ms, sound_volume, tts_read,
                        layout, style, text_color, highlight_color, font_family,
                        font_size, text_align
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(platform, alert_type) DO UPDATE SET
                        enabled=excluded.enabled,
                        sound_path=excluded.sound_path,
                        media_path=excluded.media_path,
                        text_template=excluded.text_template,
                        duration_ms=excluded.duration_ms,
                        sound_volume=excluded.sound_volume,
                        tts_read=excluded.tts_read,
                        layout=excluded.layout,
                        style=excluded.style,
                        text_color=excluded.text_color,
                        highlight_color=excluded.highlight_color,
                        font_family=excluded.font_family,
                        font_size=excluded.font_size,
                        text_align=excluded.text_align
                """, data)
                conn.commit()

            for c in configs:
                self._cache[(c.platform.lower(), c.alert_type.lower())] = c
            logger.debug("[AlertStorage] Batch saved %d alert configs", len(configs))
            return True
        except Exception as e:
            logger.error("[AlertStorage] Error batch saving alert configs: %s", e)
            return False
