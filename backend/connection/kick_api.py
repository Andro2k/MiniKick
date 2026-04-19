import requests
from curl_cffi import requests as cffi_requests

def obtener_mi_perfil(access_token):
    """
    Llama a la API oficial de Kick (sin parámetros) 
    para obtener el nombre de usuario del dueño del token.
    """
    url = "https://api.kick.com/public/v1/channels"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                return data[0].get("slug") # Devuelve el username en minúsculas
    except Exception as e:
        print(f"[-] Error al consultar perfil: {e}")
        
    return None

def obtener_chatroom_id(streamer_slug):
    """
    Técnica de scraping interno para burlar a Cloudflare
    y extraer el chatroom ID necesario para Pusher.
    """
    url = f"https://kick.com/api/v1/channels/{streamer_slug}"
    
    try:
        # Engañamos a Cloudflare simulando ser Chrome
        response = cffi_requests.get(url, impersonate="chrome124", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("chatroom", {}).get("id")
    except Exception as e:
        print(f"[-] Error al buscar Chatroom ID: {e}")
        
    return None

def obtener_recompensas_kick(access_token):
    """Obtiene la lista completa de recompensas del canal para mostrarlas en la app."""
    url = "https://api.kick.com/public/v1/channels/rewards"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"[-] Error API Rewards: {response.text}")
    except Exception as e:
        print(f"[-] Error de red al leer recompensas: {e}")
    return []

def obtener_canjes_pendientes(access_token):
    """Consulta si alguien acaba de canjear un punto (Estado: Pending)."""
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions?status=pending"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"[-] Error de red al leer canjes: {e}")
    return []

def aceptar_canje_kick(access_token, redemption_ids):
    """Le dice a Kick que los puntos ya salieron en pantalla y se cobraron con éxito."""
    url = "https://api.kick.com/public/v1/channels/rewards/redemptions/accept"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Kick espera que "ids" sea una lista, por ejemplo: ["id1", "id2"]
    payload = {"ids": redemption_ids}
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return True
        else:
            print(f"[-] Error de la API de Kick al aceptar canje: HTTP {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[-] Error de red aceptando canje: {e}")
    return False