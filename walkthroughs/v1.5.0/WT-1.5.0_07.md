# Walkthrough: Switches de Activación/Desactivación de TTS por Rol y Optimización de Layout en Chat

## Resumen de las Mejoras

Se implementó el filtrado selectivo de lectura por voz (TTS) para cada rol de usuario y se optimizó el layout y dimensionamiento vertical/horizontal del panel en [`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py).

---

### 1. Optimización de Dimensiones y Layout ([`tts_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/tts_settings.py))
- **Eliminación del desbordamiento horizontal y vertical**:
  - `row_provider` (Motor de Voz TTS) se migró al componente responsivo `VoiceSettingRow`, eliminando el ancho mínimo rígido de `180px` que causaba que el dropdown de motor se desbordara del borde de la tarjeta al achicar la ventana.
  - Se eliminaron las descripciones estáticas redundantes de cada rol que añadían peso visual y espacio innecesario, simplificando la firma de `VoiceSettingRow`.
  - Se compactaron márgenes internos y espaciados (`margin=8, spacing=4`), reduciendo el tamaño del botón de prueba a `28x28px`.
  - La tarjeta completa de Ajustes de Voz cabe fluidamente en la pantalla sin requerir scroll vertical en resoluciones estándar.

- **Fila Integrada Horizontal**:
  - Cada rol presenta: `[ Switch ]` + `[ ComboBox de Voz (Expandible) ]` + `[ Botón de Prueba ]`.

---

### 2. Limpieza de Claves i18n
- Se eliminaron las claves de descripción no utilizadas (`broadcaster_desc`, `moderator_desc`, `subscriber_desc`, `vip_desc`, `provider_desc`, `voice_general_desc`) de `locales/es.json`, `locales/en.json` y `default_en_locale.py`.
- Se verificó la paridad e integridad de traducciones al 100%.

---

### 3. Proporciones y Stretch en [`chat_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py)
- Se ajustó el ancho mínimo del contenedor izquierdo a `440px`.
- Se equilibró el ratio de `stretch` a `1:1` para que el panel de configuración de la izquierda tenga suficiente anchura sin achicarse ni comprimir los controles.

---

### 4. Persistencia y Filtrado en Tiempo Real ([`chat_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py) & [`tts_voice_handler.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/tts_voice_handler.py))
- Almacenamiento local persistente para los booleanos de cada rol (`tts_role_enabled_*`).
- `is_role_enabled(badges, settings)` filtra en tiempo $O(1)$ los mensajes según el rol antes de activar la síntesis de voz.

---

## Verificación

- Suite completa de pruebas unitarias (`uv run pytest`):
  - **53 / 53 pruebas aprobadas** (100% éxito).
