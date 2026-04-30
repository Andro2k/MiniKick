# backend/database.py

import os
import json
import sqlite3
from pathlib import Path
from typing import Any

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
            # Tabla de tokens existente
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    raw_json TEXT NOT NULL
                )
            ''')
            
            # --- Configuración General (Alta Cohesión) ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS general_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
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

class SQLiteSettingsStorage:
    def __init__(self, db_manager: DatabaseManager):
        self.db_path = db_manager.db_path

    def _save(self, key: str, value: Any) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Guardamos como string, ya que SQLite maneja textos mejor
            val_str = str(value)
            cursor.execute('''
                INSERT INTO general_settings (key, value) 
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, val_str))
            conn.commit()

    def _load(self, key: str, default: Any) -> Any:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM general_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return default

    def save_bool(self, key: str, value: bool) -> None:
        # Convertimos boolean a 'true'/'false' string para SQLite
        self._save(key, 'true' if value else 'false')

    def load_bool(self, key: str, default: bool) -> bool:
        val = self._load(key, None)
        if val is None:
            return default
        return val == 'true'

    def save_string(self, key: str, value: str) -> None:
        self._save(key, value)

    def load_string(self, key: str, default: str) -> str:
        val = self._load(key, None)
        return default if val is None else str(val)