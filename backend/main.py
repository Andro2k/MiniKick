from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import edge_tts
import os
import time

app = FastAPI(title="Motor TTS para MiniKick")

# Apuntamos a la carpeta media que está un nivel arriba del backend
AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media", "audios"))
os.makedirs(AUDIO_DIR, exist_ok=True)

class Mensaje(BaseModel):
    texto: str
    voz: str = "es-MX-JorgeNeural" 

@app.post("/generar-tts")
async def generar_tts(mensaje: Mensaje):
    try:
        filename = f"mensaje_{int(time.time())}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)

        communicate = edge_tts.Communicate(mensaje.texto, mensaje.voz)
        await communicate.save(filepath)

        return {
            "status": "success", 
            "archivo": filename, 
            "mensaje": f"Audio generado correctamente en {filepath}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))