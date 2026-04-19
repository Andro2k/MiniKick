from backend.database import iniciar_db, cargar_sesion, guardar_sesion
from backend.auth import autenticar_usuario
from backend.kick_api import obtener_mi_perfil, obtener_chatroom_id
from backend.chat import iniciar_chat

if __name__ == "__main__":
    print("=== MiniKick: Arquitectura Modular (TTS Activado) ===")
    
    # 1. Preparar la base de datos local
    iniciar_db()
    sesion = cargar_sesion()

    # 2. Si no hay sesión, hacemos el flujo completo
    if not sesion:
        print("[!] No hay sesión guardada.")
        tokens = autenticar_usuario()
        
        if tokens:
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            
            print("[*] Identificando tu canal en Kick...")
            mi_usuario = obtener_mi_perfil(access_token)
            
            if mi_usuario:
                print(f"[+] Hola, {mi_usuario}! Buscando tu Chatroom ID...")
                mi_chatroom = obtener_chatroom_id(mi_usuario)
                
                if mi_chatroom:
                    guardar_sesion(access_token, refresh_token, mi_usuario, mi_chatroom)
                    sesion = cargar_sesion() 
                else:
                    print("[-] Fallo al obtener el Chatroom ID.")
            else:
                print("[-] Fallo al leer tu perfil.")
        else:
            print("[-] Autenticación cancelada.")
            exit()
    
    # 3. Arrancar el chat si hay sesión válida
    if sesion:
        print(f"\n[+] BIENVENIDO: {sesion['username']}")
        print(f"[*] Escuchando Chatroom ID: {sesion['chatroom_id']}")
        iniciar_chat(sesion['chatroom_id'])