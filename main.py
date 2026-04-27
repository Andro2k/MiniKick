import os
import threading

from dotenv import load_dotenv

from backend.auth import AuthManager
from backend.chat import ChatManager
from backend.tts import TTSManager

load_dotenv()


def run() -> None:
    # 1. Auth
    auth = AuthManager(
        client_id=os.getenv("KICK_CLIENT_ID"),
        client_secret=os.getenv("KICK_CLIENT_SECRET"),
        redirect_uri=os.getenv("KICK_REDIRECT_URI"),
    )
    tokens = auth.get_tokens()

    # 2. TTS — inicia su propio hilo interno
    tts = TTSManager(rate=150)

    # 3. Chat
    chat = ChatManager(
        token=tokens["access_token"],
        cluster=os.getenv("KICK_PUSHER_CLUSTER"),
        key=os.getenv("KICK_PUSHER_KEY"),
    )
    username, room_id = chat.get_user_data()
    print(f"[*] Bot activo: {username} (ID: {room_id})")

    def on_new_chat_msg(user: str, msg: str) -> None:
        if msg:
            print(f"[CHAT] {user}: {msg}")
            tts.say(f"{user} dice {msg}")   # API limpia, sin exponer la queue

    # 4. Socket en hilo separado
    socket_thread = threading.Thread(
        target=chat.start_socket,
        args=(room_id, on_new_chat_msg),
        daemon=True,
    )
    socket_thread.start()

    print("[+] Escuchando... Presiona Ctrl+C para salir.")
    try:
        socket_thread.join()   # Bloquea en el hilo del socket en vez de un busy-loop
    except KeyboardInterrupt:
        print("\n[-] Saliendo...")
        tts.stop()


if __name__ == "__main__":
    run()