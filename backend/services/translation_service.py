# backend/services/translation_service.py

import json
import os

class TranslationService:
    """Carga y provee cadenas de texto basadas en el idioma seleccionado."""
    
    def __init__(self, locales_dir: str = "locales", default_lang: str = "es"):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.locales_dir = os.path.join(base_dir, locales_dir)
        self.current_lang = default_lang
        self._texts = {}
        os.makedirs(self.locales_dir, exist_ok=True)
        self.load_language(default_lang)

    def load_language(self, lang_code: str) -> bool:
        """Carga en memoria el diccionario JSON del idioma solicitado."""
        filepath = os.path.join(self.locales_dir, f"{lang_code}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._texts = json.load(f)
            self.current_lang = lang_code
            return True
        except FileNotFoundError:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"[i18n] Archivo {lang_code}.json creado automáticamente.")
            return False

    def get(self, key: str, default: str = "") -> str:
        """Navega por el JSON usando puntos. Ejemplo: get('menu.settings.title')"""
        keys = key.split('.')
        val = self._texts
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default or key 
        return str(val)