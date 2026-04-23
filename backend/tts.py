import asyncio
import os
import queue
import threading
import uuid
import edge_tts
import pygame

# Ocultar el mensaje de bienvenida de pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

class TTSManager:
    """Gestiona la cola de texto a voz y la reproducción de audio."""
    
    def __init__(self):
        self.tts_queue = queue.Queue()
        self._thread = None
        self._is_running = False
        self._mixer_initialized = False

    def _init_mixer(self):
        """Inicializa Pygame de forma diferida (lazy load)."""
        if not self._mixer_initialized:
            pygame.mixer.init()
            self._mixer_initialized = True

    async def _generar_audio(self, texto, voz, ruta_archivo):
        """Corrutina para generar el audio con Edge TTS."""
        comunicador = edge_tts.Communicate(texto, voz)
        await comunicador.save(ruta_archivo)

    def _worker_tts(self):
        """Hilo de trabajo que procesa la cola secuencialmente."""
        self._init_mixer()
        
        while self._is_running:
            try:
                # El timeout nos permite revisar _is_running sin quedarnos bloqueados para siempre
                paquete = self.tts_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # Señal de apagado
            if paquete is None:
                self.tts_queue.task_done()
                break
                
            texto, voz = paquete
            
            # Crear un nombre de archivo único para evitar conflictos de lectura/escritura
            archivo_temp = f"temp_tts_{uuid.uuid4().hex[:8]}.mp3"
            
            try:
                # asyncio.run() es la forma moderna y segura de correr funciones async
                asyncio.run(self._generar_audio(texto, voz, archivo_temp))
                
                # Reproducir el audio
                pygame.mixer.music.load(archivo_temp)
                pygame.mixer.music.play()
                
                # Esperar activamente a que termine la reproducción
                while pygame.mixer.music.get_busy() and self._is_running:
                    pygame.time.Clock().tick(10)
                    
                # Liberar el archivo
                pygame.mixer.music.unload()
                
            except Exception as e:
                print(f"[!] Error en el proceso TTS: {e}")
                
            finally:
                # Limpieza: borrar el archivo físico siempre, ocurra o no un error
                if os.path.exists(archivo_temp):
                    try:
                        os.remove(archivo_temp)
                    except OSError:
                        pass
                
                self.tts_queue.task_done()

    def iniciar(self):
        """Arranca el hilo en segundo plano si no está corriendo."""
        if self._thread is None or not self._thread.is_alive():
            self._is_running = True
            self._thread = threading.Thread(target=self._worker_tts, daemon=True)
            self._thread.start()

    def detener(self):
        """Apaga el hilo de forma segura."""
        self._is_running = False
        # Insertamos un paquete nulo (veneno) para destrabar el queue.get() inmediatamente
        self.tts_queue.put(None) 

    def hablar(self, texto, voz="es-MX-JorgeNeural"):
        """Añade un texto a la cola de reproducción."""
        if not self._is_running:
            self.iniciar() # Auto-arranque si se intenta hablar sin iniciar
        self.tts_queue.put((texto, voz))


# ==========================================
# WRAPPERS PARA MANTENER COMPATIBILIDAD
# ==========================================
tts_instance = TTSManager()

def hablar(texto, voz="es-MX-JorgeNeural"):
    """
    Función envoltorio para que no tengas que cambiar tu código del frontend.
    Simplemente llama al método hablar de la instancia.
    """
    tts_instance.hablar(texto, voz)

def detener_tts():
    """Para apagar el motor cuando cierres MiniKick."""
    tts_instance.detener()