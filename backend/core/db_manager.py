# backend/core/db_manager.py
import sqlite3
import os

class DBManager:
    """Gestor centralizado para la base de datos SQLite del bot."""
    
    def __init__(self, db_name="database.sqlite"):
        # 1. Obtenemos la ruta de AppData/Local dependiendo del sistema operativo
        if os.name == 'nt':  # Si es Windows
            appdata_local = os.getenv('LOCALAPPDATA')
        else:  # Fallback por si lo ejecutas en Mac o Linux
            appdata_local = os.path.join(os.path.expanduser('~'), '.local', 'share')
            
        # 2. Definimos la ruta completa de tu carpeta: AppData/Local/MiniKick
        self.app_dir = os.path.join(appdata_local, "MiniKick")
        
        # 3. Definimos la ruta final de la base de datos
        self.db_path = os.path.join(self.app_dir, db_name)
        
        # 4. Creamos la carpeta MiniKick si no existe
        os.makedirs(self.app_dir, exist_ok=True)
        
        # Inicializamos las tablas
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Crea las tablas si no existen al iniciar la aplicación."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tabla CONFIG (Clave-Valor para Tokens, y configuraciones del TTS)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # 2. Tabla TRIGGERS (Recompensas y Alertas)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS triggers (
                    name TEXT PRIMARY KEY,
                    file TEXT,
                    type TEXT,
                    volume INTEGER,
                    cost INTEGER,
                    color TEXT,
                    description TEXT,
                    enabled BOOLEAN,
                    scale REAL,
                    pos_x INTEGER,
                    pos_y INTEGER,
                    random BOOLEAN,
                    kick_id TEXT
                )
            ''')

            # 3. Tabla TTS BLACKLIST (Usuarios que el bot no leerá)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tts_blacklist (
                    username TEXT PRIMARY KEY
                )
            ''')
            
            conn.commit()

    # ==========================================
    # ⚙️ MÉTODOS PARA CONFIGURACIONES GLOBALES (TTS Y TOKENS)
    # ==========================================
    
    def get_config(self, key: str, default=None):
        """Obtiene un valor de configuración (ej: 'tts_volume', 'tts_rate')."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_config(self, key: str, value):
        """Guarda o actualiza un valor (ej: set_config('tts_voice', 'es-MX-JorgeNeural'))."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO config (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, str(value)))
            conn.commit()

    # ==========================================
    # 🚫 MÉTODOS PARA LA BLACKLIST DEL TTS
    # ==========================================

    def add_ignored_user(self, username: str):
        """Añade un usuario a la lista de ignorados del TTS."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO tts_blacklist (username) VALUES (?)", (username.lower().strip(),))
            conn.commit()

    def remove_ignored_user(self, username: str):
        """Quita a un usuario de la lista de ignorados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tts_blacklist WHERE username = ?", (username.lower().strip(),))
            conn.commit()

    def get_ignored_users(self) -> list:
        """Devuelve una lista con todos los usuarios ignorados."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM tts_blacklist")
            return [row[0] for row in cursor.fetchall()]

    # ==========================================
    # 🎁 MÉTODOS PARA LOS TRIGGERS (RECOMPENSAS)
    # ==========================================

    def save_trigger(self, trigger_data: dict):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO triggers 
                (name, file, type, volume, cost, color, description, enabled, scale, pos_x, pos_y, random, kick_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET 
                    file=excluded.file, type=excluded.type, volume=excluded.volume, 
                    cost=excluded.cost, color=excluded.color, description=excluded.description, 
                    enabled=excluded.enabled, scale=excluded.scale, 
                    pos_x=excluded.pos_x, pos_y=excluded.pos_y, random=excluded.random, kick_id=excluded.kick_id
            """, (
                trigger_data.get('name'), 
                trigger_data.get('file'), 
                trigger_data.get('type'),
                trigger_data.get('volume', 100), 
                trigger_data.get('cost', 100), 
                trigger_data.get('color', ''),
                trigger_data.get('description', ''), 
                trigger_data.get('enabled', True),
                trigger_data.get('scale', 1.0),
                trigger_data.get('pos_x', 0), 
                trigger_data.get('pos_y', 0), 
                trigger_data.get('random', False),
                trigger_data.get('kick_id', '')
            ))
            conn.commit()

    def get_all_triggers(self) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM triggers")
            columns = [col[0] for col in cursor.description]
            triggers_dict = {}
            for row in cursor.fetchall():
                data = dict(zip(columns, row))
                data['enabled'] = bool(data['enabled'])
                data['random'] = bool(data['random'])
                name = data.pop('name')
                triggers_dict[name] = data
            return triggers_dict

    def delete_trigger(self, name: str):
        """Elimina un trigger de la base de datos."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM triggers WHERE name = ?", (name.lower().strip(),))
            conn.commit()