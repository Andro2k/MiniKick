# frontend/workers/fetch_rewards_worker.py

from PySide6.QtCore import QThread, Signal
from backend.kick_api_client import KickAPIClient

class FetchRewardsWorker(QThread):
    rewards_fetched = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, api_client: KickAPIClient, parent=None):
        super().__init__(parent)
        self.setObjectName("Worker_Fetch_Rewards")
        self.api_client = api_client
        self._is_shutting_down = False

    def run(self):
        try:
            resp = self.api_client.fetch_channel_rewards()
            rewards = [item["title"] for item in resp.get("data", [])]
            self.rewards_fetched.emit(rewards)
        except Exception as e:
            self.error_occurred.emit(str(e))