import asyncio
import os
import queue
import threading
import edge_tts
import pygame

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
pygame.mixer.init()

tts_queue = queue.Queue()

def worker_tts():
    while True:
        # Ahora extraemos una tupla (texto, voz)
        paquete = tts_queue.get() 
        if paquete is None:
            break
            
        texto, voz = paquete
        archivo_temp = "temp_tts.mp3"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            comunicador = edge_tts.Communicate(texto, voz)
            loop.run_until_complete(comunicador.save(archivo_temp))
            
            pygame.mixer.music.load(archivo_temp)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.unload()
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
                
        except Exception as e:
            print(f"[!] Error en el TTS: {e}")
            
        finally:
            tts_queue.task_done()

hilo_tts = threading.Thread(target=worker_tts, daemon=True)
hilo_tts.start()

def hablar(texto, voz="es-MX-JorgeNeural"):
    """Envía el texto y la voz deseada a la fila de reproducción."""
    tts_queue.put((texto, voz))