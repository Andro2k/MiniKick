import json
import websocket
import time
import re
from urllib.parse import urlparse
from backend.connection.config import PUSHER_KEY, PUSHER_CLUSTER
from backend.tts import hablar

# Variables globales de control
config_actual = {}
debe_continuar = True
ws_app_actual = None  # <-- NUEVO: Guardaremos la conexión aquí para poder matarla

def limpiar_mensaje(texto):
    """Limpia emotes y procesa links para el TTS."""
    texto = re.sub(r'\[emote:\d+:[^\]]+\]', '', texto)
    def procesar_link(match):
        dominio = urlparse(match.group(0)).netloc.replace('www.', '')
        return f" enlace de {dominio} "
    texto = re.sub(r'http[s]?://\S+', procesar_link, texto)
    return texto.strip()

def actualizar_config_en_vivo(nueva_config):
    """Permite cambiar la voz o el modo sin desconectar el bot."""
    global config_actual
    config_actual.update(nueva_config)

def on_message(ws, message, callback_gui):
    try:
        data = json.loads(message)
        if data.get("event") == "pusher:ping":
            ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
            return
            
        if data.get("event") == "App\\Events\\ChatMessageEvent":
            chat_data = json.loads(data.get("data", "{}"))
            usuario = chat_data.get("sender", {}).get("username", "Desconocido")
            contenido = chat_data.get("content", "")

            # 1. ENVIAR A LA GUI
            if callback_gui:
                callback_gui(usuario, contenido)

            # 2. LÓGICA DE LECTURA
            modo = config_actual.get("modo", "auto")
            comando = config_actual.get("comando", "!s")
            voz = config_actual.get("voz", "es-MX-JorgeNeural")

            debe_leer = False
            texto_a_hablar = contenido

            if modo == "auto":
                debe_leer = True
            elif modo == "comando" and contenido.lower().startswith(comando.lower() + " "):
                debe_leer = True
                texto_a_hablar = contenido[len(comando):].strip()

            if debe_leer:
                limpio = limpiar_mensaje(texto_a_hablar)
                if limpio:
                    hablar(f"{usuario} dice: {limpio}", voz)
    except Exception as e:
        print(f"[!] Error: {e}")

def iniciar_chat(chatroom_id, configuracion, callback_gui=None):
    global config_actual, debe_continuar, ws_app_actual
    config_actual = configuracion
    debe_continuar = True

    ws_url = f"wss://ws-{PUSHER_CLUSTER}.pusher.com/app/{PUSHER_KEY}?protocol=7&client=js&version=8.4.0-rc2&flash=false"

    while debe_continuar:
        try:
            # Guardamos la aplicación WebSocket en la variable global
            ws_app_actual = websocket.WebSocketApp(
                ws_url,
                on_open=lambda ws: ws.send(json.dumps({
                    "event": "pusher:subscribe", 
                    "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}
                })),
                on_message=lambda ws, msg: on_message(ws, msg, callback_gui)
            )
            
            # Esto bloquea el hilo hasta que se cierre la conexión
            ws_app_actual.run_forever(ping_interval=30, ping_timeout=10)
            
            # Al cerrarse, comprobamos si fue voluntario
            if not debe_continuar: break
            time.sleep(3)
        except Exception as e:
            if not debe_continuar: break
            time.sleep(5)

def detener_chat():
    """Fuerza el cierre inmediato de la conexión WebSocket."""
    global debe_continuar, ws_app_actual
    debe_continuar = False
    
    # Si hay una conexión activa, la cerramos físicamente
    if ws_app_actual:
        ws_app_actual.close()