# backend\storage\rewards_storage.py

from backend.database.manager import DatabaseManager

class SQLiteRewardsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_all(self) -> dict:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos FROM obs_rewards")
            return {r[0]: {"filepath": r[1], "volume": r[2], "scale": r[3], "pos_x": r[4], "pos_y": r[5], "is_random_pos": bool(r[6])} for r in cursor.fetchall()}

    def save_all(self, mappings: dict) -> None:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM obs_rewards")
            data = [
                (
                    reward,
                    conf.get("filepath", ""),
                    conf.get("volume", 1.0),
                    conf.get("scale", 1.0),
                    conf.get("pos_x", 0),
                    conf.get("pos_y", 0),
                    int(conf.get("is_random_pos", False))
                )
                for reward, conf in mappings.items()
            ]
            cursor.executemany(
                "INSERT INTO obs_rewards (reward_name, filepath, volume, scale, pos_x, pos_y, is_random_pos) VALUES (?, ?, ?, ?, ?, ?, ?)",
                data
            )
            conn.commit()
