import requests
from curl_cffi import requests as cffi_requests
from backend.database import cargar_sesion, actualizar_tokens
from backend.connection.auth import renovar_token

def hacer_peticion_kick(url, method="GET", payload=None, token_override=None):
    """
    Función maestra (Wrapper) para hacer peticiones a Kick.
    Maneja automáticamente la renovación del token si expira.
    """
    if token_override:
        # Se usa durante el primer login cuando la sesión aún no está guardada
        access_token = token_override
        refresh_token = None
    else:
        # Modo normal: Carga de la BD
        sesion = cargar_sesion()
        if not sesion: return None
        access_token = sesion['access_token']
        refresh_token = sesion['refresh_token']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    # 1. Hacer la petición original
    if method == "POST":
        headers["Content-Type"] = "application/json"
        response = requests.post(url, headers=headers, json=payload)
    else:
        response = requests.get(url, headers=headers)

    # 2. Si el token expiró (401) e intentamos usar una sesión guardada
    if response.status_code == 401 and refresh_token:
        print("[*] Access Token caducado. Intentando renovar con Refresh Token...")
        nuevos_tokens = renovar_token(refresh_token)

        if nuevos_tokens:
            print("[+] Token renovado con éxito en segundo plano. Guardando y reintentando...")
            # Guardamos en base de datos
            actualizar_tokens(nuevos_tokens['access_token'], nuevos_tokens['refresh_token'])
            
            # Actualizamos el header y REINTENTAMOS la petición
            headers["Authorization"] = f"Bearer {nuevos_tokens['access_token']}"
            if method == "POST":
                response = requests.post(url, headers=headers, json=payload)
            else:
                response = requests.get(url, headers=headers)
        else:
            print("[-] El Refresh Token también caducó o es inválido. Toca re-loguearse manualmente.")
            return None

    # 3. Procesar la respuesta final
    if response.status_code == 200:
        try:
            return response.json()
        except:
            return True # Algunas respuestas de Kick (como aceptar canje) no devuelven JSON útil
            
    print(f"[-] Error en API Kick (HTTP {response.status_code}): {response.text}")
    return None

# ==========================================
# FUNCIONES REFACCIONADAS (Usan el Wrapper)
# ==========================================

def obtener_mi_perfil(access_token):
    url = "https://api.kick.com/public/v1/channels"
    # Pasamos el token directamente porque aquí aún no hay sesión en la DB
    data = hacer_peticion_kick(url, token_override=access_token) 
    if data and "data" in data and len(data["data"]) > 0:
        return data["data"][0].get("slug")
    return None

def obtener_chatroom_id(streamer_slug):
    url = f"https://kick.com/api/v1/channels/{streamer_slug}"
    try:
        response = cffi_requests.get(url, impersonate="chrome124", timeout=10)
        if response.status_code == 200:
            return response.json().get("chatroom", {}).get("id")
    except Exception as e:
        print(f"[-] Error al buscar Chatroom ID: {e}")
    return None

def obtener_recompensas_kick(access_token=None):
    # Ya no necesita el access_token como parámetro, el wrapper lo busca, 
    # pero lo dejamos en la firma por si otras partes de tu código lo envían.
    url = "https://api.kick.com/public/v1/channels/rewards"
    data = hacer_peticion_kick(url)
    return data.get("data", []) if data else []

def obtener_canjes_pendientes(access_token=None):
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions?status=pending"
    data = hacer_peticion_kick(url)
    return data.get("data", []) if data else []

def aceptar_canje_kick(access_token, redemption_ids):
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions/accept"
    payload = {"ids": redemption_ids}
    return hacer_peticion_kick(url, method="POST", payload=payload) is not None