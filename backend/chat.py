import json
import time
import re
from urllib.parse import urlparse
import websocket

# Importamos la clase Config refactorizada
from backend.connection.config import Config
from backend.tts import hablar

def limpiar_mensaje(texto):
    """Limpia emotes y procesa links para el TTS."""
    # Eliminar formato de emotes de Kick
    texto = re.sub(r'\[emote:\d+:[^\]]+\]', '', texto)
    
    def procesar_link(match):
        dominio = urlparse(match.group(0)).netloc.replace('www.', '')
        return f" enlace de {dominio} "
        
    texto = re.sub(r'http[s]?://\S+', procesar_link, texto).strip()
    
    # Limpiar espacios en blanco dobles que dejan los emotes al borrarse
    return re.sub(r'\s+', ' ', texto)

class ChatListener:
    """Encapsula la conexión al chat para evitar variables globales."""
    
    def __init__(self):
        self.config = {}
        self.debe_continuar = False
        self.ws_app = None
        self.callback_gui = None

    def actualizar_config(self, nueva_config):
        """Permite cambiar la voz o el modo sin desconectar el bot."""
        self.config.update(nueva_config)

    def _on_message(self, ws, message):
        """Manejador interno de los mensajes del WebSocket."""
        try:
            data = json.loads(message)
            
            # 1. Mantener la conexión viva (Heartbeat)
            if data.get("event") == "pusher:ping":
                ws.send(json.dumps({"event": "pusher:pong", "data": {}}))
                return
                
            # 2. Procesar eventos de chat
            if data.get("event") == "App\\Events\\ChatMessageEvent":
                chat_data = json.loads(data.get("data", "{}"))
                usuario = chat_data.get("sender", {}).get("username", "Desconocido")
                contenido = chat_data.get("content", "")

                # Enviar a la interfaz gráfica
                if self.callback_gui:
                    self.callback_gui(usuario, contenido)

                # Lógica de lectura TTS
                modo = self.config.get("modo", "auto")
                comando = self.config.get("comando", "!s")
                voz = self.config.get("voz", "es-MX-JorgeNeural")

                debe_leer = False
                texto_a_hablar = contenido

                if modo == "auto":
                    debe_leer = True
                elif modo == "comando":
                    # Chequeamos si empieza con el comando seguido de un espacio
                    if contenido.lower().startswith(f"{comando.lower()} "):
                        debe_leer = True
                        texto_a_hablar = contenido[len(comando):].strip()
                    # O si es exactamente solo el comando
                    elif contenido.lower() == comando.lower():
                        debe_leer = True
                        texto_a_hablar = "" 

                if debe_leer:
                    limpio = limpiar_mensaje(texto_a_hablar)
                    if limpio:
                        hablar(f"{usuario} dice: {limpio}", voz)
                        
        except json.JSONDecodeError:
            print("[-] Error al decodificar JSON del chat de Kick.")
        except Exception as e:
            print(f"[!] Error inesperado procesando mensaje de chat: {e}")

    def iniciar(self, chatroom_id, configuracion, callback_gui=None):
        """Inicia la conexión WebSocket con Kick/Pusher y maneja reconexiones."""
        self.config = configuracion
        self.callback_gui = callback_gui
        self.debe_continuar = True

        # Usamos Config.PUSHER_CLUSTER y Config.PUSHER_KEY
        ws_url = f"wss://ws-{Config.PUSHER_CLUSTER}.pusher.com/app/{Config.PUSHER_KEY}?protocol=7&client=js&version=8.4.0-rc2&flash=false"

        def on_open(ws):
            print("[+] Conectado al Chat de Kick. Suscribiéndose...")
            ws.send(json.dumps({
                "event": "pusher:subscribe", 
                "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}
            }))

        while self.debe_continuar:
            try:
                self.ws_app = websocket.WebSocketApp(
                    ws_url,
                    on_open=on_open,
                    on_message=self._on_message
                )
                
                # Bloquea el hilo hasta que se pierda o cierre la conexión
                self.ws_app.run_forever(ping_interval=30, ping_timeout=10)
                
                # Si salió del bucle run_forever pero debe_continuar es True, reconecta
                if not self.debe_continuar: 
                    break
                    
                print("[*] Desconexión del chat detectada. Reconectando en 3s...")
                time.sleep(3)
                
            except Exception as e:
                print(f"[-] Error en el hilo del WebSocket: {e}")
                if not self.debe_continuar: 
                    break
                time.sleep(5)

    def detener(self):
        """Fuerza el cierre inmediato de la conexión WebSocket."""
        self.debe_continuar = False
        if self.ws_app:
            print("[*] Cerrando conexión del chat de forma segura...")
            self.ws_app.close()

# ==========================================
# WRAPPERS PARA MANTENER COMPATIBILIDAD
# ==========================================
# Creamos una única instancia del listener. 
# Esto evita que tengas que cambiar el código en tu interfaz gráfica (GUI).
chat_listener_instance = ChatListener()

def iniciar_chat(chatroom_id, configuracion, callback_gui=None):
    chat_listener_instance.iniciar(chatroom_id, configuracion, callback_gui)

def detener_chat():
    chat_listener_instance.detener()

def actualizar_config_en_vivo(nueva_config):
    chat_listener_instance.actualizar_config(nueva_config)