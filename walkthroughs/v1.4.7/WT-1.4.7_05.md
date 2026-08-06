# Walkthrough WT-1.4.7_05 - Corrección del Combobox de Región en TTS

## Resumen

Se solucionó la superposición del desplegable de regiones (`es-ES`) en la esquina superior izquierda del panel de TTS.

## Cambios Aplicados

1. **[locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)** & **[locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)**:
   - Se agregaron traducciones `"lang_title"` y `"lang_desc"`.

2. **[frontend/components/chat/tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)**:
   - Se integró `self.combo_lang` dentro de un `SettingRow` visible dentro de la tarjeta `voices_card`.
