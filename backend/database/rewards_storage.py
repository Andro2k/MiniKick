# backend\database\rewards_storage.py

import logging
from .database_manager import DatabaseManager

logger = logging.getLogger("minikick.database.rewards_storage")

class SQLiteRewardsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos, thumbnail_bytes,
                           reward_id, cost, description, background_color, is_user_input_required, platform
                    FROM obs_rewards
                """)
                result = {}
                for r in cursor.fetchall():
                    reward_name = r[0]
                    platform = r[13] if len(r) > 13 and r[13] else "kick"
                    conf = {
                        "name": reward_name,
                        "filepath": r[1],
                        "volume": r[2],
                        "scale": r[3],
                        "pos_x": r[4],
                        "pos_y": r[5],
                        "is_random_pos": bool(r[6]),
                        "thumbnail_bytes": r[7],
                        "platform": platform
                    }
                    if r[8] is not None:
                        conf["id"] = r[8]
                    if r[9] is not None:
                        conf["cost"] = r[9]
                    if r[10] is not None:
                        conf["description"] = r[10]
                    if r[11] is not None:
                        conf["background_color"] = r[11]
                    if r[12] is not None:
                        conf["is_user_input_required"] = bool(r[12])
                    key = f"{platform}:{reward_name}"
                    result[key] = conf
                return result
        except Exception as e:
            logger.error("[RewardsStorage] Error loading all rewards: %s", e)
            return {}

    def save_all(self, mappings: dict) -> None:
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM obs_rewards")
                data = []
                for key, conf in mappings.items():
                    if not isinstance(conf, dict):
                        continue
                    reward_name = conf.get("name") or conf.get("reward_name")
                    if not reward_name:
                        if isinstance(key, str) and ":" in key:
                            _, reward_name = key.split(":", 1)
                        elif isinstance(key, tuple):
                            reward_name = str(key[1])
                        else:
                            reward_name = str(key)

                    platform = conf.get("platform")
                    if not platform:
                        if isinstance(key, str) and ":" in key:
                            platform = key.split(":", 1)[0]
                        elif isinstance(key, tuple):
                            platform = str(key[0])
                        else:
                            platform = "kick"

                    data.append((
                        reward_name,
                        conf.get("filepath", ""),
                        conf.get("volume", 1.0),
                        conf.get("scale", 1.0),
                        conf.get("pos_x", 0),
                        conf.get("pos_y", 0),
                        int(conf.get("is_random_pos", False)),
                        conf.get("thumbnail_bytes", None),
                        conf.get("id"),
                        conf.get("cost", 100),
                        conf.get("description", ""),
                        conf.get("background_color", "#00e701"),
                        int(conf.get("is_user_input_required", False)),
                        platform
                    ))
                cursor.executemany(
                    """INSERT INTO obs_rewards 
                       (reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos, thumbnail_bytes, reward_id, cost, description, background_color, is_user_input_required, platform) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    data
                )
                conn.commit()
            logger.debug("[RewardsStorage] Saved %d reward mappings", len(mappings))
        except Exception as e:
            logger.error("[RewardsStorage] Error saving reward mappings: %s", e)
