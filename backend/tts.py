import asyncio
import os
import queue
import threading
import edge_tts
import pygame

# Inicializar el motor de audio de pygame (ocultando su mensaje de bienvenida)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
pygame.mixer.init()

# Creamos una cola (fila) para que los audios no se sobrepongan
tts_queue = queue.Queue()

# Voz natural en Español (Puedes cambiarla a 'es-ES-AlvaroNeural' para acento de España)
VOZ_TTS = "es-MX-JorgeNeural" 

def worker_tts():
    """Este hilo corre de fondo reproduciendo los mensajes en orden."""
    while True:
        texto = tts_queue.get() # Espera hasta que haya un mensaje en la fila
        if texto is None:
            break
            
        archivo_temp = "temp_tts.mp3"
        
        try:
            # 1. edge-tts es asíncrono, así que creamos un bucle de eventos para él
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            comunicador = edge_tts.Communicate(texto, VOZ_TTS)
            loop.run_until_complete(comunicador.save(archivo_temp))
            
            # 2. Reproducir el audio generado
            pygame.mixer.music.load(archivo_temp)
            pygame.mixer.music.play()
            
            # 3. Esperar a que termine de hablar antes de pasar al siguiente mensaje
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # 4. Limpieza: soltar el archivo y borrarlo para no llenar el disco duro
            pygame.mixer.music.unload()
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)
                
        except Exception as e:
            print(f"[!] Error en el TTS: {e}")
            
        finally:
            tts_queue.task_done()

# Arrancamos el trabajador en segundo plano automáticamente al importar el módulo
hilo_tts = threading.Thread(target=worker_tts, daemon=True)
hilo_tts.start()

def hablar(texto):
    """Función pública: Simplemente agrega el texto a la fila y vuelve al chat inmediatamente."""
    tts_queue.put(texto)