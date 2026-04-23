import time
import threading
import requests
import urllib.parse
from backend.connection.kick_api import obtener_canjes_pendientes, aceptar_canje_kick
from backend.database import obtener_vinculos_recompensas

# Es buena práctica tener la URL del servidor local de OBS como constante
OBS_SERVER_URL = "http://127.0.0.1:8081"

class RewardsListener:
    """Gestiona la escucha de recompensas en un hilo en segundo plano."""
    
    def __init__(self):
        # Un 'Event' es mucho más seguro que usar variables booleanas globales
        self._stop_event = threading.Event()
        self._thread = None

    def limpiar_pendientes_al_iniciar(self):
        """Busca todos los canjes acumulados y los marca como aceptados sin activarlos."""
        print("[*] Revisando si hay canjes antiguos pendientes...")
        
        # Ya no le pasamos el token, la API lo busca sola
        canjes_agrupados = obtener_canjes_pendientes() 
        
        if canjes_agrupados:
            todos_los_ids = []
            for grupo in canjes_agrupados:
                redemptions = grupo.get('redemptions', [])
                for red in redemptions:
                    todos_los_ids.append(red.get('id'))
            
            if todos_los_ids:
                print(f"[*] Limpiando {len(todos_los_ids)} canjes antiguos del historial...")
                # Aceptamos hasta 25 por petición (límite de la API de Kick)
                for i in range(0, len(todos_los_ids), 25):
                    bloque = todos_los_ids[i:i + 25]
                    aceptar_canje_kick(bloque)
                print("[+] Historial limpio. El bot escuchará solo canjes nuevos.")

    def _loop_recompensas(self):
        """Bucle principal que se ejecuta en el hilo."""
        self.limpiar_pendientes_al_iniciar()

        # Mientras el evento de parada NO esté activo...
        while not self._stop_event.is_set():
            try:
                canjes_agrupados = obtener_canjes_pendientes()
                
                if canjes_agrupados:
                    vinculos = obtener_vinculos_recompensas()
                    mapa_vinculos = {v['reward_id']: v for v in vinculos}

                    for grupo in canjes_agrupados:
                        reward_id = grupo.get('reward', {}).get('id')
                        redemptions = grupo.get('redemptions', [])

                        if reward_id in mapa_vinculos and redemptions:
                            vinculo = mapa_vinculos[reward_id]
                            ids_a_aceptar = []

                            for red in redemptions:
                                ids_a_aceptar.append(red.get('id'))
                                
                                # 4. Disparar alerta en OBS leyendo los ajustes personalizados
                                url_media = f"{OBS_SERVER_URL}/serve_media?path={urllib.parse.quote(vinculo['path'])}"
                                payload = {
                                    "action": "play_media",
                                    "type": vinculo['type'],
                                    "url": url_media,
                                    "volume": vinculo['volume'],       
                                    "random": vinculo['is_random'],    
                                    "scale": vinculo['scale'],         
                                    "pos_x": vinculo['pos_x'],         
                                    "pos_y": vinculo['pos_y'],         
                                    "filename": vinculo['name']
                                }
                                
                                try:
                                    # Hemos cambiado el bare "except: pass" por algo más controlado
                                    requests.post(f"{OBS_SERVER_URL}/api/trigger", json=payload, timeout=5)
                                    print(f"[+] Alerta enviada a OBS: {vinculo['name']}")
                                except requests.exceptions.RequestException as e:
                                    print(f"[-] Error enviando alerta a OBS: {e}")
                                
                                # Si en medio de procesar varios canjes cierran la app, salimos rápido
                                if self._stop_event.is_set(): 
                                    break
                                time.sleep(1) # Pausa entre alertas

                            # Solo marcamos como aceptados si hemos procesado las IDs (y ya no pasamos el token)
                            if ids_a_aceptar:
                                aceptar_canje_kick(ids_a_aceptar)
                                
            except Exception as e:
                print(f"[-] Error inesperado en bucle de recompensas: {e}")
            
            # EL TRUCO ESTRELLA: En lugar de usar time.sleep(5), usamos wait(5). 
            # Esto pausa el bucle 5 segundos, PERO si cerramos el bot, 
            # despierta instantáneamente y se apaga de golpe, sin tener que esperar.
            self._stop_event.wait(5)

    def iniciar(self):
        """Inicia el hilo si no está corriendo ya."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._loop_recompensas, daemon=True)
            self._thread.start()
            print("[+] Escuchador de Puntos de Canal INICIADO.")

    def detener(self):
        """Señala al hilo que debe detenerse."""
        if self._thread and self._thread.is_alive():
            print("[*] Deteniendo escuchador de recompensas...")
            self._stop_event.set() # Activa la señal para detener el bucle
            # No usamos join() aquí para no bloquear la interfaz gráfica al cerrar

# ==========================================
# WRAPPERS PARA MANTENER COMPATIBILIDAD
# ==========================================
listener_instance = RewardsListener()

def iniciar_escucha_recompensas():
    listener_instance.iniciar()

def detener_escucha_recompensas():
    listener_instance.detener()