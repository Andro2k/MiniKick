import json
import websocket
import time
from backend.connection.config import PUSHER_KEY, PUSHER_CLUSTER
from backend.tts import hablar

def on_message(ws, message):
    try:
        data = json.loads(message)
        evento = data.get("event")
        
        # El latido del corazón para no desconectarnos
        if evento == "pusher:ping":
            ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
            return
            
        # Suscripción exitosa
        elif evento == "pusher_internal:subscription_succeeded":
            mensaje_bienvenida = "Conexión con Kick completada exitosamente. Sistema en línea."
            print(f"[+] {mensaje_bienvenida}\n" + "="*50)
            hablar(mensaje_bienvenida) # ¡Hacemos que el bot hable al iniciar!
            
        # Mensaje de chat nuevo
        elif evento == "App\\Events\\ChatMessageEvent":
            chat_data = json.loads(data.get("data", "{}"))
            usuario = chat_data.get("sender", {}).get("username", "Desconocido")
            contenido = chat_data.get("content", "")
            
            print(f"[{usuario}]: {contenido}")
            
            # Enviar el formato a la voz (Ej: "theandro2k dice: hola")
            # Más adelante podemos poner un filtro de groserías aquí antes de pasarlo al TTS
            texto_a_hablar = f"{usuario} dice: {contenido}"
            hablar(texto_a_hablar)
            
    except Exception as e:
        print(f"[!] Error en el socket: {e}")

def iniciar_chat(chatroom_id):
    ws_url = f"wss://ws-{PUSHER_CLUSTER}.pusher.com/app/{PUSHER_KEY}?protocol=7&client=js&version=8.4.0-rc2&flash=false"

    # Envolvemos todo en un bucle infinito
    while True:
        try:
            wsapp = websocket.WebSocketApp(
                ws_url,
                on_open=lambda ws: ws.send(json.dumps({
                    "event": "pusher:subscribe", 
                    "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}
                })),
                on_message=on_message,
                on_error=lambda ws, e: print(f"[!] Error de conexión: {e}"),
                on_close=lambda ws, a, b: print("\n[*] Desconectado del servidor de chat.")
            )

            # Esto correrá hasta que Pusher nos desconecte
            wsapp.run_forever(ping_interval=30, ping_timeout=10)

            # Si llegamos a esta línea, es porque Pusher cerró la conexión.
            print("[*] Intentando reconectar en 3 segundos...")
            time.sleep(3) # Pausa breve para no saturar al servidor

        except Exception as e:
            print(f"[!] Error crítico en el bucle principal: {e}")
            time.sleep(5)