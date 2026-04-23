import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Clase centralizada para las configuraciones de MiniKick."""
    
    # Credenciales Kick
    CLIENT_ID = os.getenv("KICK_CLIENT_ID")
    CLIENT_SECRET = os.getenv("KICK_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("KICK_REDIRECT_URI")
    PORT = int(os.getenv("PORT", 8080))

    # Credenciales Pusher
    PUSHER_KEY = os.getenv("KICK_PUSHER_KEY")
    PUSHER_CLUSTER = os.getenv("KICK_PUSHER_CLUSTER", "us2")

    # Base de datos
    DB_FILE = "minikick.db"

    @classmethod
    def validar_credenciales(cls):
        """Verifica que las variables esenciales existan antes de arrancar."""
        faltantes = []
        if not cls.CLIENT_ID: faltantes.append("KICK_CLIENT_ID")
        if not cls.CLIENT_SECRET: faltantes.append("KICK_CLIENT_SECRET")
        if not cls.REDIRECT_URI: faltantes.append("KICK_REDIRECT_URI")
        
        if faltantes:
            print(f"[-] Error Crítico: Faltan las siguientes variables en el archivo .env: {', '.join(faltantes)}")
            sys.exit(1) # Detiene la ejecución si faltan credenciales vitales

# Opcional: Llamar a la validación automáticamente al importar (si es seguro para tu flujo)
# Config.validar_credenciales()