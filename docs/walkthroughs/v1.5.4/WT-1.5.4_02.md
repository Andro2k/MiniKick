# Walkthrough: Integración de Piper TTS y Gestor de Voces a Demanda en MiniKick

## 1. Resumen de la Implementación

Se completó exitosamente la integración de **Piper TTS** como el nuevo proveedor principal de voz local neuronal en MiniKick, junto con un **Gestor y Descargador de Voces a Demanda** y manteniendo **Windows SAPI5 (`pyttsx3`)** como motor de respaldo y **Edge-TTS** como motor en la nube.

---

## 2. Componentes y Módulos Creados/Actualizados

### 1. Capa de Datos / Proveedor (`Data Access & Provider Layer`):
- `backend/providers/voices/tts_piper.py`:
  - Implementación completa de `ITTSProvider` (`speak`, `prepare`, `stop`, `set_volume`, `get_available_voices`, `set_audio_device`).
  - Cache en memoria $\mathcal{O}(1)$ de modelos ONNX cargados (`_loaded_models`) para evitar lecturas repetidas de disco.
  - Generación de audio a archivos temporales y reproducción fluida a través de `QMediaPlayer` y `QAudioOutput` con compatibilidad total de dispositivos de salida de audio configurados en MiniKick.

### 2. Catálogo y Lógica de Negocio (`Business Logic Layer`):
- `backend/services/chat/piper_voice_manager.py`:
  - Catálogo preconfigurado con las mejores voces en Español e Inglés:
    - 🇪🇸 `es_ES-davefx-medium` (Voz predeterminada recomendada • 60.3 MB)
    - 🇪🇸 `es_ES-sharvard-medium` (Español España - Natural • 41.5 MB)
    - 🇪🇸 `es_ES-carlfm-x_low` (Español España - Ultra ligera • 16.8 MB)
    - 🇲🇽 `es_MX-ald-medium` (Español México - Neutro • 60.1 MB)
    - 🇲🇽 `es_MX-claude-high` (Español México - Alta calidad • 115.0 MB)
    - 🇺🇸 `en_US-lessac-medium` (Inglés US - Claro • 35.2 MB)
    - 🇺🇸 `en_US-amy-medium` (Inglés US - Femenina • 35.1 MB)
  - `PiperVoiceDownloadWorker(QThread)` para descargas asíncronas seguras con reportes de progreso y capacidad de cancelación.
  - Verificación y eliminación de modelos en $\mathcal{O}(1)$.

### 3. Capa de Servicios y Handlers (`Service & Handler Layer`):
- `backend/services/chat/tts_service.py`:
  - `TTSManager` ahora gestiona `"piper"`, `"web"` y `"local"`, con invalidación dinámica de caché de voces al descargar nuevos modelos.
- `backend/handlers/tts_voice_handler.py`:
  - Soporte de conmutación entre los 3 motores y apertura del diálogo de gestión de voces Piper.

### 4. Capa de Presentación / UI (`Presentation/UI Layer`):
- `frontend/dialogs/piper_voices_dialog.py`:
  - Modal moderno sin marco con catálogo de voces, etiquetas de idioma, tamaño en MB, estado de instalación, botón de prueba de voz y barra de progreso en vivo durante la descarga.
- `frontend/components/chat/tts_settings.py`:
  - Selector de 3 opciones en `combo_provider` y botón de acceso directo con icono de descarga para abrir el gestor de voces.

### 5. Internacionalización (i18n):
- Actualizados `locales/es.json` y `locales/en.json` con paridad total de claves y cero textos hardcodeados.

---

## 3. Pruebas y Validación

- **Pruebas Unitarias Ejecutadas**:
  - `tests/unit/test_piper_voice_manager.py` (Catálogo, resolución de rutas, estado instalado y worker de descarga).
  - `tests/unit/test_tts_piper_provider.py` (Inicialización, volumen, síntesis y parada).
  - `tests/unit/test_i18n_integrity.py` (Paridad de claves y existencia).
  - `tests/unit/test_roles_integrity.py` (Cumplimiento de roles QSS en el tema).
- **Resultado de la Suite**: **84 pruebas pasadas exitosamente (100% OK)**.
