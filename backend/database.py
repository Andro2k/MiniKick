import sqlite3
from contextlib import contextmanager
from backend.connection.config import Config

@contextmanager
def get_db_connection():
    """Context manager para manejar las conexiones a la base de datos de forma segura."""
    conexion = sqlite3.connect(Config.DB_FILE)
    # Permite acceder a los resultados como diccionarios en lugar de tuplas
    conexion.row_factory = sqlite3.Row 
    try:
        yield conexion
    finally:
        conexion.close()

def iniciar_db():
    with get_db_connection() as conexion:
        cursor = conexion.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesion (
                id INTEGER PRIMARY KEY,
                access_token TEXT, refresh_token TEXT,
                username TEXT, chatroom_id INTEGER,
                voz_tts TEXT, modo_lectura TEXT, comando_tts TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recompensas_media (
                reward_id TEXT PRIMARY KEY,
                reward_name TEXT,
                media_type TEXT,
                media_path TEXT,
                volume INTEGER DEFAULT 100,
                scale REAL DEFAULT 1.0,
                is_random BOOLEAN DEFAULT 1,
                pos_x INTEGER DEFAULT 0,
                pos_y INTEGER DEFAULT 0
            )
        ''')
        conexion.commit()

def guardar_vinculo_recompensa(reward_id, reward_name, media_type, media_path):
    with get_db_connection() as conexion:
        cursor = conexion.cursor()
        cursor.execute("SELECT reward_id FROM recompensas_media WHERE reward_id = ?", (reward_id,))
        
        if cursor.fetchone():
            cursor.execute('''
                UPDATE recompensas_media 
                SET reward_name = ?, media_type = ?, media_path = ? 
                WHERE reward_id = ?
            ''', (reward_name, media_type, media_path, reward_id))
        else:
            cursor.execute('''
                INSERT INTO recompensas_media (reward_id, reward_name, media_type, media_path, volume, scale, is_random, pos_x, pos_y)
                VALUES (?, ?, ?, ?, 100, 1.0, 1, 0, 0)
            ''', (reward_id, reward_name, media_type, media_path))
        conexion.commit()

def actualizar_ajustes_recompensa(reward_id, volume, scale, is_random, pos_x, pos_y):
    with get_db_connection() as conexion:
        conexion.execute('''
            UPDATE recompensas_media
            SET volume = ?, scale = ?, is_random = ?, pos_x = ?, pos_y = ?
            WHERE reward_id = ?
        ''', (volume, scale, is_random, pos_x, pos_y, reward_id))
        conexion.commit()

def obtener_vinculos_recompensas():
    with get_db_connection() as conexion:
        cursor = conexion.execute('SELECT * FROM recompensas_media')
        filas = cursor.fetchall()
        
        # Gracias a sqlite3.Row, podemos extraer los datos directamente por la clave
        return [{
            "reward_id": f["reward_id"], 
            "name": f["reward_name"], 
            "type": f["media_type"], 
            "path": f["media_path"],
            "volume": f["volume"], 
            "scale": f["scale"], 
            "is_random": bool(f["is_random"]), 
            "pos_x": f["pos_x"], 
            "pos_y": f["pos_y"]
        } for f in filas]

def eliminar_vinculo_recompensa(reward_id):
    with get_db_connection() as conexion:
        conexion.execute('DELETE FROM recompensas_media WHERE reward_id = ?', (reward_id,))
        conexion.commit()

def guardar_sesion(access_token, refresh_token, username, chatroom_id, voz_tts="es-MX-JorgeNeural", modo_lectura="auto", comando_tts="!s"):
    with get_db_connection() as conexion:
        conexion.execute('DELETE FROM sesion')
        conexion.execute('''
            INSERT INTO sesion (access_token, refresh_token, username, chatroom_id, voz_tts, modo_lectura, comando_tts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (access_token, refresh_token, username, chatroom_id, voz_tts, modo_lectura, comando_tts))
        conexion.commit()

def actualizar_configuracion(voz_tts, modo_lectura, comando_tts):
    with get_db_connection() as conexion:
        conexion.execute('''
            UPDATE sesion 
            SET voz_tts = ?, modo_lectura = ?, comando_tts = ?
        ''', (voz_tts, modo_lectura, comando_tts))
        conexion.commit()

def cargar_sesion():
    with get_db_connection() as conexion:
        cursor = conexion.execute('SELECT * FROM sesion LIMIT 1')
        resultado = cursor.fetchone()
        
        if resultado:
            return {
                "access_token": resultado["access_token"],
                "refresh_token": resultado["refresh_token"],
                "username": resultado["username"],
                "chatroom_id": resultado["chatroom_id"],
                "voz_tts": resultado["voz_tts"] or "es-MX-JorgeNeural",
                "modo_lectura": resultado["modo_lectura"] or "auto",
                "comando_tts": resultado["comando_tts"] or "!s"
            }
        return None

def borrar_sesion():
    with get_db_connection() as conexion:
        conexion.execute('DELETE FROM sesion')
        conexion.commit()

def actualizar_tokens(access_token, refresh_token):
    with get_db_connection() as conexion:
        conexion.execute('''
            UPDATE sesion 
            SET access_token = ?, refresh_token = ?
        ''', (access_token, refresh_token)) 
        conexion.commit()