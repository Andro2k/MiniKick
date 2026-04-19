import json
import requests
import os

TOKEN_FILE = "kick_token.json"

def leer_canal_oficial(streamer_slug):
    # 1. Cargar el token que generamos con auth_kick.py
    if not os.path.exists(TOKEN_FILE):
        print("[-] Error: No se encontró el archivo kick_token.json. Ejecuta la autenticación primero.")
        return

    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)
        
    access_token = token_data.get("access_token")

    # 2. Configurar la petición según la documentación de Kick
    # Endpoint oficial de Kick Dev API
    url = f"https://api.kick.com/public/v1/channels?slug={streamer_slug}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    print(f"[*] Consultando API Oficial para el canal: {streamer_slug}...")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # La API devuelve un array en la propiedad 'data'
            canales = data.get("data", [])
            
            if canales:
                info_canal = canales[0]
                print("\n[+] ¡Datos obtenidos con éxito!")
                print(f"    - Streamer: {info_canal.get('slug')}")
                print(f"    - ID del Broadcaster: {info_canal.get('broadcaster_user_id')}")
                print(f"    - Título del Stream: {info_canal.get('stream_title', 'Sin título')}")
                
                # Verificamos si está en vivo
                stream = info_canal.get("stream")
                if stream and stream.get("is_live"):
                    print(f"    - ESTADO: EN VIVO (Espectadores: {stream.get('viewer_count')})")
                    print(f"    - Categoría: {info_canal.get('category', {}).get('name')}")
                else:
                    print("    - ESTADO: OFFLINE")
            else:
                print("[-] La API no devolvió datos para este canal.")
                
        elif response.status_code == 401:
            print("[-] Error 401: No autorizado. Tu Access Token podría haber expirado.")
        else:
            print(f"[-] Error HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"[-] Error de conexión: {e}")

if __name__ == "__main__":
    print("=== MiniKick Lector de API Oficial ===")
    streamer = input("Ingresa el nombre del streamer: ").strip().lower()
    leer_canal_oficial(streamer)