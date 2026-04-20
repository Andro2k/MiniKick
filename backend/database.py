import sqlite3
from backend.connection.config import DB_FILE

def iniciar_db():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    
    # Tabla de sesión
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesion (
            id INTEGER PRIMARY KEY,
            access_token TEXT, refresh_token TEXT,
            username TEXT, chatroom_id INTEGER,
            voz_tts TEXT, modo_lectura TEXT, comando_tts TEXT
        )
    ''')
    
    # TABLA RECOMPENSAS ACTUALIZADA (Añadido volumen, escala, random, pos_x, pos_y)
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
    conexion.close()

def guardar_vinculo_recompensa(reward_id, reward_name, media_type, media_path):
    """Guarda una nueva recompensa, respetando los ajustes si ya existía."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    
    cursor.execute("SELECT reward_id FROM recompensas_media WHERE reward_id = ?", (reward_id,))
    if cursor.fetchone():
        cursor.execute('''
            UPDATE recompensas_media SET reward_name = ?, media_type = ?, media_path = ? WHERE reward_id = ?
        ''', (reward_name, media_type, media_path, reward_id))
    else:
        cursor.execute('''
            INSERT INTO recompensas_media (reward_id, reward_name, media_type, media_path, volume, scale, is_random, pos_x, pos_y)
            VALUES (?, ?, ?, ?, 100, 1.0, 1, 0, 0)
        ''', (reward_id, reward_name, media_type, media_path))
    conexion.commit()
    conexion.close()

def actualizar_ajustes_recompensa(reward_id, volume, scale, is_random, pos_x, pos_y):
    """Guarda los ajustes personalizados desde el Modal."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE recompensas_media
        SET volume = ?, scale = ?, is_random = ?, pos_x = ?, pos_y = ?
        WHERE reward_id = ?
    ''', (volume, scale, is_random, pos_x, pos_y, reward_id))
    conexion.commit()
    conexion.close()

def obtener_vinculos_recompensas():
    """Devuelve todas las recompensas con todos sus ajustes."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('SELECT reward_id, reward_name, media_type, media_path, volume, scale, is_random, pos_x, pos_y FROM recompensas_media')
    filas = cursor.fetchall()
    conexion.close()
    
    return [{
        "reward_id": f[0], "name": f[1], "type": f[2], "path": f[3],
        "volume": f[4], "scale": f[5], "is_random": bool(f[6]), "pos_x": f[7], "pos_y": f[8]
    } for f in filas]

def eliminar_vinculo_recompensa(reward_id):
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM recompensas_media WHERE reward_id = ?', (reward_id,))
    conexion.commit()
    conexion.close()

def guardar_sesion(access_token, refresh_token, username, chatroom_id, voz_tts="es-MX-JorgeNeural", modo_lectura="auto", comando_tts="!s"):
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM sesion')
    cursor.execute('''
        INSERT INTO sesion (access_token, refresh_token, username, chatroom_id, voz_tts, modo_lectura, comando_tts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (access_token, refresh_token, username, chatroom_id, voz_tts, modo_lectura, comando_tts))
    conexion.commit()
    conexion.close()

def actualizar_configuracion(voz_tts, modo_lectura, comando_tts):
    """Actualiza solo las configuraciones sin tocar los tokens de sesión."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE sesion 
        SET voz_tts = ?, modo_lectura = ?, comando_tts = ?
    ''', (voz_tts, modo_lectura, comando_tts))
    conexion.commit()
    conexion.close()

def cargar_sesion():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('SELECT access_token, refresh_token, username, chatroom_id, voz_tts, modo_lectura, comando_tts FROM sesion LIMIT 1')
    resultado = cursor.fetchone()
    conexion.close()
    
    if resultado:
        return {
            "access_token": resultado[0],
            "refresh_token": resultado[1],
            "username": resultado[2],
            "chatroom_id": resultado[3],
            "voz_tts": resultado[4] or "es-MX-JorgeNeural",
            "modo_lectura": resultado[5] or "auto",
            "comando_tts": resultado[6] or "!s"
        }
    return None

def borrar_sesion():
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM sesion')
    conexion.commit()
    conexion.close()

def actualizar_tokens(access_token, refresh_token):
    """Actualiza los tokens de acceso cuando expiran, manteniendo el resto de la sesión."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    # Ahora sí le pasamos las variables al final del execute
    cursor.execute('''
        UPDATE sesion 
        SET access_token = ?, refresh_token = ?
    ''', (access_token, refresh_token)) 
    conexion.commit()
    conexion.close()