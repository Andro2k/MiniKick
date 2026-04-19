# backend/rewards_listener.py
import time
import threading
import requests
import urllib.parse
from backend.connection.kick_api import obtener_canjes_pendientes, aceptar_canje_kick
from backend.database import obtener_vinculos_recompensas, cargar_sesion

escuchando = False
hilo_recompensas = None

def limpiar_pendientes_al_iniciar(access_token):
    """Busca todos los canjes acumulados y los marca como aceptados sin activarlos."""
    print("[*] Revisando si hay canjes antiguos pendientes...")
    canjes_agrupados = obtener_canjes_pendientes(access_token)
    
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
                aceptar_canje_kick(access_token, bloque)
            print("[+] Historial limpio. El bot escuchará solo canjes nuevos.")

def loop_recompensas():
    sesion = cargar_sesion()
    if not sesion: return
    
    access_token = sesion['access_token']
    
    # --- PASO NUEVO: LIMPIEZA INICIAL ---
    limpiar_pendientes_al_iniciar(access_token)

    while escuchando:
        try:
            canjes_agrupados = obtener_canjes_pendientes(access_token)
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
                            url_media = f"http://127.0.0.1:8081/serve_media?path={urllib.parse.quote(vinculo['path'])}"
                            payload = {
                                "action": "play_media",
                                "type": vinculo['type'],
                                "url": url_media,
                                "volume": vinculo['volume'],       # <--- NUEVO
                                "random": vinculo['is_random'],    # <--- NUEVO
                                "scale": vinculo['scale'],         # <--- NUEVO
                                "pos_x": vinculo['pos_x'],         # <--- NUEVO
                                "pos_y": vinculo['pos_y'],         # <--- NUEVO
                                "filename": vinculo['name']
                            }
                            
                            try:
                                requests.post("http://127.0.0.1:8081/api/trigger", json=payload)
                                print(f"[+] Alerta enviada: {vinculo['name']}")
                            except: pass
                            
                            time.sleep(1) # Pausa entre alertas

                        if ids_a_aceptar:
                            aceptar_canje_kick(access_token, ids_a_aceptar)
        except Exception as e:
            print(f"[-] Error en bucle: {e}")
        
        time.sleep(5)

def iniciar_escucha_recompensas():
    global escuchando, hilo_recompensas
    if not escuchando:
        escuchando = True
        hilo_recompensas = threading.Thread(target=loop_recompensas, daemon=True)
        hilo_recompensas.start()
        print("[+] Escuchador de Puntos de Canal INICIADO.")

def detener_escucha_recompensas():
    global escuchando
    escuchando = False