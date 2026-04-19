import sqlite3
from backend.connection.config import DB_FILE

def iniciar_db():
    """Crea la tabla de sesión si no existe."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sesion (
            id INTEGER PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            username TEXT,
            chatroom_id INTEGER
        )
    ''')
    conexion.commit()
    conexion.close()

def guardar_sesion(access_token, refresh_token, username, chatroom_id):
    """Guarda o sobrescribe la sesión actual del usuario."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    # Solo permitimos una sesión activa, así que borramos cualquier dato viejo
    cursor.execute('DELETE FROM sesion')
    cursor.execute('''
        INSERT INTO sesion (access_token, refresh_token, username, chatroom_id)
        VALUES (?, ?, ?, ?)
    ''', (access_token, refresh_token, username, chatroom_id))
    conexion.commit()
    conexion.close()

def cargar_sesion():
    """Devuelve un diccionario con los datos de sesión si existen, o None."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('SELECT access_token, refresh_token, username, chatroom_id FROM sesion LIMIT 1')
    resultado = cursor.fetchone()
    conexion.close()
    
    if resultado:
        return {
            "access_token": resultado[0],
            "refresh_token": resultado[1],
            "username": resultado[2],
            "chatroom_id": resultado[3]
        }
    return None

def borrar_sesion():
    """Cierra la sesión borrando los datos de la base local."""
    conexion = sqlite3.connect(DB_FILE)
    cursor = conexion.cursor()
    cursor.execute('DELETE FROM sesion')
    conexion.commit()
    conexion.close()