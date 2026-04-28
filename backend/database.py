# backend/database.py

import os
import json
import sqlite3
from pathlib import Path

class DatabaseManager:
    """Gestiona la conexión y creación de la base de datos local (Alta Cohesión)"""
    def __init__(self):
        self.db_path = self._get_appdata_path()
        self._init_db()

    def _get_appdata_path(self) -> Path:
        """Resuelve la ruta correcta según el sistema operativo (SoR)"""
        if os.name == 'nt':  # Windows
            base_dir = Path(os.getenv('LOCALAPPDATA', Path.home()))
        else:  # Mac / Linux
            base_dir = Path.home() / '.config'
            
        app_dir = base_dir / '.Minikick' / 'data'
        app_dir.mkdir(parents=True, exist_ok=True) # Crea las carpetas si no existen
        
        return app_dir / 'minikick.db'

    def _init_db(self):
        """Crea las tablas necesarias si es la primera vez que se ejecuta"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Tabla para los tokens (Solo habrá un registro con ID 1)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    raw_json TEXT NOT NULL
                )
            ''')
            conn.commit()


class SQLiteTokenStorage:
    """
    Cumple el contrato de TokenStorage (Inversión de Dependencias).
    El AuthManager usará esto sin saber que es una base de datos.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_path = db_manager.db_path

    def load(self) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT raw_json FROM tokens WHERE id = 1")
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
        return None

    def save(self, tokens: dict) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            raw_json = json.dumps(tokens)
            # INSERT OR REPLACE: Actualiza si ya existe, inserta si es nuevo
            cursor.execute('''
                INSERT INTO tokens (id, raw_json) 
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET raw_json=excluded.raw_json
            ''', (raw_json,))
            conn.commit()