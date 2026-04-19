import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import edge_tts

app = FastAPI(title="Motor TTS Portable")

# RUTA DINÁMICA: Calcula la ruta basada en donde está este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "..", "media", "audios")

# Asegurar que la carpeta exista
os.makedirs(AUDIO_DIR, exist_ok=True)

class Mensaje(BaseModel):
    texto: str
    voz: str = "es-MX-JorgeNeural" 

@app.post("/generar-tts")
async def generar_tts(mensaje: Mensaje):
    try:
        filename = f"tts_{int(time.time())}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        communicate = edge_tts.Communicate(mensaje.texto, mensaje.voz)
        await communicate.save(filepath)

        return {
            "status": "success", 
            "archivo": filename
        }
    except Exception as e:
        print(f"Error en Python: {e}")
        raise HTTPException(status_code=500, detail=str(e))