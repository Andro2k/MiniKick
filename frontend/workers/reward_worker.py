# frontend/workers/reward_worker.py

import time
from PySide6.QtCore import QThread, Signal
from backend.chat_manager import KickAPIClient

class RewardWorker(QThread):
    """Hilo dedicado a consultar periódicamente los canjes de puntos de canal."""
    # Señal: Nombre del usuario, Nombre de la recompensa, Mensaje del usuario (si hay)
    reward_redeemed = Signal(str, str, str)
    error_occurred = Signal(str)

    def __init__(self, api_client: KickAPIClient, poll_interval_seconds: int = 15):
        super().__init__()
        self.api_client = api_client
        self.poll_interval = poll_interval_seconds
        self._running = False
        self._processed_ids = set() # Memoria local para no repetir TTS

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
                        
                        # Si ya se procesó en esta sesión, lo ignoramos por seguridad
                        if red_id in self._processed_ids:
                            continue
                            
                        user_id = red.get("redeemer", {}).get("user_id", "Alguien")
                        user_input = red.get("user_input", "")
                        
                        # 1. Guardar en la caché local en memoria
                        self._processed_ids.add(red_id)
                        # 2. Agregar a la lista para limpiar en Kick
                        new_ids_to_accept.append(red_id)
                        
                        # 3. Notificar a la UI / Trigger de sonido de inmediato
                        self.reward_redeemed.emit(str(user_id), reward_title, user_input)
                
                # --- LIMPIEZA EN EL SERVIDOR DE KICK ---
                if new_ids_to_accept:
                    # La documentación de Kick exige un máximo de 25 IDs únicos por petición.
                    # Hacemos una segmentación limpia (batching) en trozos de 25.
                    for i in range(0, len(new_ids_to_accept), 25):
                        batch = new_ids_to_accept[i:i+25]
                        try:
                            self.api_client.accept_redemptions(batch)
                            print(f"🧹 Se marcaron exitosamente {len(batch)} canjes como completados en Kick.")
                        except Exception as api_err:
                            print(f"⚠️ No se pudo confirmar el lote en Kick: {api_err}")
                
            except Exception as e:
                self.error_occurred.emit(f"Error consultando recompensas: {str(e)}")
            
            # Pausa inteligente del bucle
            for _ in range(self.poll_interval * 2):
                if not self._running:
                    break
                time.sleep(0.5)

    def stop(self):
        self._running = False