# backend/services/translation_service.py

import json
import os
from backend.default_es import DEFAULT_DICTIONARY

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
        """Carga en memoria el diccionario JSON. Si no existe, lo recrea usando el diccionario de emergencia."""
        filepath = os.path.join(self.locales_dir, f"{lang_code}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._texts = json.load(f)
            self.current_lang = lang_code
            return True
        except FileNotFoundError:
            print(f"[i18n] Archivo {lang_code}.json no encontrado. Auto-reparando...")
            
            fallback_data = DEFAULT_DICTIONARY if lang_code == "es" else {}
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fallback_data, f, indent=4, ensure_ascii=False)
            
            self._texts = fallback_data
            self.current_lang = lang_code
            return False

    def get(self, key: str) -> str:
        """Navega por el JSON usando puntos. Si no lo encuentra, devuelve la misma llave."""
        keys = key.split('.')
        val = self._texts
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return key
        return str(val)