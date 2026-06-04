# frontend/workers/reward_worker.py

import time
from PySide6.QtCore import QThread, Signal
from backend.kick_api_client import KickAPIClient

class RewardWorker(QThread):
    reward_redeemed = Signal(str, str, str)
    error_occurred = Signal(str)

    # Añadimos parent=None y super().__init__(parent)
    def __init__(self, api_client: KickAPIClient, poll_interval_seconds: int = 15, parent=None):
        super().__init__(parent) 
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
                    reward_title = item.get("reward", {}).get("title", "Recompensa desconocida")
                    redemptions = item.get("redemptions", [])
                    
                    for red in redemptions:
                        red_id = red.get("id")

                        if red_id in self._processed_ids:
                            continue
                            
                        user_id = red.get("redeemer", {}).get("user_id", "Alguien")
                        user_input = red.get("user_input", "")

                        self._processed_ids.add(red_id)
                        new_ids_to_accept.append(red_id)
                        self.reward_redeemed.emit(str(user_id), reward_title, user_input)
                
                if new_ids_to_accept:
                    for i in range(0, len(new_ids_to_accept), 25):
                        batch = new_ids_to_accept[i:i+25]
                        try:
                            self.api_client.accept_redemptions(batch)
                            print(f"🧹 Se marcaron exitosamente {len(batch)} canjes como completados en Kick.")
                        except Exception as api_err:
                            print(f"⚠️ No se pudo confirmar el lote en Kick: {api_err}")
                
            except Exception as e:
                self.error_occurred.emit(f"Error consultando recompensas: {str(e)}")

            for _ in range(self.poll_interval * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def stop(self):
        self._running = False