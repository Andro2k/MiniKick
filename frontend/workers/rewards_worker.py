# frontend\workers\reward_worker.py

import time
from PySide6.QtCore import QThread, Signal
from backend.providers.kick.kick_client import KickAPIClient

class RewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
    error_occurred = Signal(str)

    def __init__(self, i18n, api_client: KickAPIClient, poll_interval_seconds: int = 15, parent=None):
        super().__init__(parent) 
        self.i18n = i18n
        self.setObjectName("Worker_Reward_Polling") 
        self.api_client = api_client
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._processed_ids = set() 

    def run(self):
        self._running = True
        
        while self._running:
            try:
                response = self.api_client.fetch_pending_redemptions()
                data_list = response.get("data", [])           
                new_ids_to_accept = []
                
                for item in data_list:
                    reward_title = item.get("reward", {}).get("title", self.i18n.get("main.workers.reward.unknown_reward"))
                    redemptions = item.get("redemptions", [])                  
                    for red in redemptions:
                        red_id = red.get("id")

                        if red_id in self._processed_ids:
                            continue            
                        user_id = red.get("redeemer", {}).get("user_id", self.i18n.get("main.workers.reward.someone"))
                        user_input = red.get("user_input", "")
                        self._processed_ids.add(red_id)
                        new_ids_to_accept.append(red_id)
                        self.reward_redeemed.emit(str(user_id), reward_title, user_input)
                
                if new_ids_to_accept:
                    for i in range(0, len(new_ids_to_accept), 25):
                        batch = new_ids_to_accept[i:i+25]
                        try:
                            self.api_client.accept_redemptions(batch)
                            print(self.i18n.get("main.workers.reward.batch_success").replace("{count}", str(len(batch))))
                        except Exception as api_err:
                            print(self.i18n.get("main.workers.reward.batch_error").replace("{error}", str(api_err)))             
            except Exception as e:
                self.error_occurred.emit(self.i18n.get("main.workers.reward.poll_error").replace("{error}", str(e)))

            for _ in range(self.poll_interval * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def stop(self):
        self._running = False

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