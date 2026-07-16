# backend\services\system\translation_service.py

import json
import logging
import os
import sys
from backend.config.default_en_locale import DEFAULT_DICTIONARY

class TranslationService:    
    def __init__(self, locales_dir: str = "locales", default_lang: str = "en"):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

        self.locales_dir = os.path.join(base_dir, locales_dir)
        self.current_lang = default_lang
        self._texts = {}
        os.makedirs(self.locales_dir, exist_ok=True)
        self.load_language(default_lang)

    def load_language(self, lang_code: str) -> bool:
        filepath = os.path.join(self.locales_dir, f"{lang_code}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self._texts = json.load(f)
            self.current_lang = lang_code
            return True
        except FileNotFoundError:
            logging.warning("[i18n] File %s.json not found. Auto-repairing...", lang_code)
            fallback_data = DEFAULT_DICTIONARY if lang_code == "en" else {}          
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fallback_data, f, indent=4, ensure_ascii=False)
            
            self._texts = fallback_data
            self.current_lang = lang_code
            return False

    def get(self, key: str) -> str:
        keys = key.split('.')
        val = self._texts
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return key
        return str(val)
