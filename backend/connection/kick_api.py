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