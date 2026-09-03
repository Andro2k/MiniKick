# backend\workers\rewards_worker.py

import logging
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("minikick.workers.rewards")

class FetchRewardsWorker(QThread):
    rewards_fetched = Signal(object, object)
    error_occurred = Signal(str)

    def __init__(self, api_client, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Fetch_Rewards_{platform}")
        self.api_client = api_client
        self.broadcaster_id = broadcaster_id
        self.platform = platform
        self._is_shutting_down = False

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.fetch_channel_rewards(self.broadcaster_id)
            else:
                resp = self.api_client.fetch_channel_rewards()

            data = resp.get("data", [])
            rewards_list = []
            rewards_map = {}
            for item in data:
                if isinstance(item, dict) and "title" in item:
                    title = item["title"]
                    item["platform"] = self.platform
                    rewards_list.append(title)
                    rewards_map[title] = item

            self.rewards_fetched.emit(rewards_list, rewards_map)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CreateRewardWorker(QThread):
    reward_created = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, payload: dict, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Create_Reward_{platform}")
        self.api_client = api_client
        self.payload = payload
        self.broadcaster_id = broadcaster_id
        self.platform = platform

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.create_channel_reward(
                    broadcaster_id=self.broadcaster_id,
                    title=self.payload.get("title", ""),
                    cost=self.payload.get("cost", 100),
                    description=self.payload.get("description", ""),
                    background_color=self.payload.get("background_color", "#9146FF"),
                    is_user_input_required=self.payload.get("is_user_input_required", False)
                )
            else:
                resp = self.api_client.create_channel_reward(
                    title=self.payload.get("title", ""),
                    cost=self.payload.get("cost", 100),
                    description=self.payload.get("description", ""),
                    background_color=self.payload.get("background_color", "#00e701"),
                    is_user_input_required=self.payload.get("is_user_input_required", False),
                    should_redemptions_skip_request_queue=self.payload.get("should_redemptions_skip_request_queue", False)
                )
            reward_data = resp.get("data", {})
            if isinstance(reward_data, dict):
                reward_data["platform"] = self.platform
            self.reward_created.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))

class UpdateRewardWorker(QThread):
    reward_updated = Signal(object)
    error_occurred = Signal(str)

    def __init__(self, api_client, reward_id: str, payload: dict, broadcaster_id: str = "", platform: str = "kick", parent=None):
        super().__init__(parent)
        self.setObjectName(f"Worker_Update_Reward_{platform}")
        self.api_client = api_client
        self.reward_id = reward_id
        self.payload = payload
        self.broadcaster_id = broadcaster_id
        self.platform = platform

    def run(self):
        try:
            if self.platform == "twitch":
                resp = self.api_client.update_channel_reward(
                    broadcaster_id=self.broadcaster_id,
                    reward_id=self.reward_id,
                    payload=self.payload
                )
            else:
                resp = self.api_client.update_channel_reward(self.reward_id, self.payload)
            reward_data = resp.get("data", {})
            if isinstance(reward_data, dict):
                reward_data["platform"] = self.platform
            self.reward_updated.emit(reward_data)
        except Exception as e:
            self.error_occurred.emit(str(e))
