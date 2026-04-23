from curl_cffi import requests
from backend.database import cargar_sesion, actualizar_tokens
from backend.connection.auth import renovar_token

def hacer_peticion_kick(url, method="GET", payload=None, token_override=None):
    """
    Función maestra (Wrapper) para hacer peticiones a Kick.
    Usa curl_cffi para evitar bloqueos de Cloudflare.
    """
    if token_override:
        access_token = token_override
        refresh_token = None
    else:
        sesion = cargar_sesion()
        if not sesion: 
            return None
        access_token = sesion['access_token']
        refresh_token = sesion['refresh_token']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    def enviar_peticion(headers_actuales):
        # Usamos impersonate='chrome124' para saltar el antibot de Kick
        if method == "POST":
            return requests.post(url, headers=headers_actuales, json=payload, impersonate="chrome124", timeout=10)
        return requests.get(url, headers=headers_actuales, impersonate="chrome124", timeout=10)

    try:
        response = enviar_peticion(headers)

        # Si el token expiró (401) e intentamos usar una sesión guardada
        if response.status_code == 401 and refresh_token:
            print("[*] Access Token caducado. Intentando renovar con Refresh Token...")
            nuevos_tokens = renovar_token(refresh_token)

            if nuevos_tokens:
                print("[+] Token renovado con éxito. Guardando y reintentando...")
                actualizar_tokens(nuevos_tokens['access_token'], nuevos_tokens['refresh_token'])
                
                headers["Authorization"] = f"Bearer {nuevos_tokens['access_token']}"
                response = enviar_peticion(headers)
            else:
                print("[-] El Refresh Token caducó. Toca re-loguearse manualmente.")
                return None

        # Procesar respuesta
        if response.status_code in [200, 201, 204]:
            try:
                return response.json()
            except ValueError:
                return True # Kick a veces devuelve 200/204 sin JSON (ej: al aceptar canjes)
                
        print(f"[-] Error en API Kick (HTTP {response.status_code}): {response.text}")
        return None

    except Exception as e:
        print(f"[-] Excepción al conectar con Kick API: {e}")
        return None

# ==========================================
# FUNCIONES REFACCIONADAS
# ==========================================

def obtener_mi_perfil(access_token):
    url = "https://api.kick.com/public/v1/channels"
    data = hacer_peticion_kick(url, token_override=access_token) 
    if data and isinstance(data, dict) and data.get("data"):
        return data["data"][0].get("slug")
    return None

def obtener_chatroom_id(streamer_slug):
    url = f"https://kick.com/api/v1/channels/{streamer_slug}"
    try:
        # Petición directa pública, no necesita autenticación
        response = requests.get(url, impersonate="chrome124", timeout=10)
        if response.status_code == 200:
            return response.json().get("chatroom", {}).get("id")
    except Exception as e:
        print(f"[-] Error al buscar Chatroom ID: {e}")
    return None

def obtener_recompensas_kick():
    url = "https://api.kick.com/public/v1/channels/rewards"
    data = hacer_peticion_kick(url)
    return data.get("data", []) if isinstance(data, dict) else []

def obtener_canjes_pendientes():
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions?status=pending"
    data = hacer_peticion_kick(url)
    return data.get("data", []) if isinstance(data, dict) else []

def aceptar_canje_kick(redemption_ids):
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions/accept"
    payload = {"ids": redemption_ids}
    return hacer_peticion_kick(url, method="POST", payload=payload) is not None