# Walkthrough WT-1.4.7_06 - Eliminación del Filtro de Idioma en Voces TTS

## Resumen

Se eliminó el filtro por idioma/región en el panel de TTS a solicitud del usuario, restaurando el comportamiento donde todas las voces (locales o Edge) se despliegan directamente en la lista de voces por rol.

## Cambios Aplicados

1. **[frontend/components/chat/tts_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py)**:
   - Eliminación del combo visual de idiomas y sus eventos asociados.

2. **[backend/handlers/tts_voice_handler.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_voice_handler.py)**:
   - Configuración de `filter_voices_by_language` para devolver el total de las voces sin filtrar.
