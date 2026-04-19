import os
from dotenv import load_dotenv

# Cargar variables de entorno una sola vez
load_dotenv()

# Credenciales de OAuth (Kick API Oficial)
CLIENT_ID = os.getenv("KICK_CLIENT_ID")
CLIENT_SECRET = os.getenv("KICK_CLIENT_SECRET")
REDIRECT_URI = os.getenv("KICK_REDIRECT_URI")
PORT = int(os.getenv("PORT", 8080))

# Credenciales de Pusher (WebSockets)
PUSHER_KEY = os.getenv("KICK_PUSHER_KEY")
PUSHER_CLUSTER = os.getenv("KICK_PUSHER_CLUSTER", "us2")

# Configuración de base de datos local
DB_FILE = "minikick.db"