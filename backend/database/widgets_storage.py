# backend\database\widgets_storage.py

import json
import logging
from .manager import DatabaseManager

logger = logging.getLogger("minikick.database.widgets")

class SQLiteWidgetsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all_widgets(self) -> dict[str, dict]:
        result = {}
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT widget_id, is_active, command, cooldown, permission, config_json 
                    FROM widgets_config
                """)
                for row in cursor.fetchall():
                    widget_id, is_active, command, cooldown, permission, config_raw = row
                    try:
                        config_data = json.loads(config_raw) if config_raw else {}
                    except json.JSONDecodeError:
                        config_data = {}
                    result[widget_id] = {
                        "widget_id": widget_id,
                        "is_active": bool(is_active),
                        "command": command,
                        "cooldown": cooldown,
                        "permission": permission,
                        "config": config_data
                    }
        except Exception as e:
            logger.error("[WidgetsStorage] Error loading all widgets: %s", e)
        return result

    def get_widget(self, widget_id: str) -> dict | None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT widget_id, is_active, command, cooldown, permission, config_json 
                    FROM widgets_config WHERE widget_id = ?
                """, (widget_id,))
                row = cursor.fetchone()
                if row:
                    widget_id, is_active, command, cooldown, permission, config_raw = row
                    try:
                        config_data = json.loads(config_raw) if config_raw else {}
                    except json.JSONDecodeError:
                        config_data = {}
                    return {
                        "widget_id": widget_id,
                        "is_active": bool(is_active),
                        "command": command,
                        "cooldown": cooldown,
                        "permission": permission,
                        "config": config_data
                    }
        except Exception as e:
            logger.error("[WidgetsStorage] Error loading widget '%s': %s", widget_id, e)
        return None

    def save_widget(self, widget_id: str, is_active: bool, command: str, cooldown: int, permission: str, config: dict) -> None:
        try:
            config_raw = json.dumps(config, ensure_ascii=False)
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO widgets_config (widget_id, is_active, command, cooldown, permission, config_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(widget_id) DO UPDATE SET
                        is_active = excluded.is_active,
                        command = excluded.command,
                        cooldown = excluded.cooldown,
                        permission = excluded.permission,
                        config_json = excluded.config_json
                """, (widget_id, 1 if is_active else 0, command.strip(), cooldown, permission, config_raw))
                conn.commit()
        except Exception as e:
            logger.error("[WidgetsStorage] Error saving widget '%s': %s", widget_id, e)
