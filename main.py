import os, threading
from dotenv import load_dotenv
from backend.auth import AuthManager
from backend.chat import ChatManager
from backend.tts import TTSManager

load_dotenv()

def run():
    # 1. Auth
    auth = AuthManager(os.getenv("KICK_CLIENT_ID"), os.getenv("KICK_CLIENT_SECRET"), os.getenv("KICK_REDIRECT_URI"))
    tokens = auth.get_tokens()

    # 2. Chat Setup
    chat = ChatManager(tokens['access_token'], os.getenv("KICK_PUSHER_CLUSTER"), os.getenv("KICK_PUSHER_KEY"))
    username, room_id = chat.get_user_data()
    print(f"[*] Bot activo: {username} (ID: {room_id})")

    # 3. TTS Setup
    tts = TTSManager()

    def on_new_chat_msg(user, msg):
        if msg:
            print(f"[CHAT] {user}: {msg}")
            tts.queue.put(f"{user} dice {msg}")

    # Ejecutar Socket en hilo separado
    threading.Thread(target=chat.start_socket, args=(room_id, on_new_chat_msg), daemon=True).start()

    # Bucle principal para el TTS (Hilo principal)
    print("[+] Escuchando... Presiona Ctrl+C para salir.")
    try:
        while True:
            tts.speak_next()
    except KeyboardInterrupt:
        print("\n[-] Saliendo...")

if __name__ == "__main__":
    run()