# Walkthrough: Controles SpinBox de Síntesis Piper TTS y Expansión de Modelos

## 1. Resumen de la Implementación
Se implementó el sistema de calibración acústica de precisión mediante `NoWheelDoubleSpinBox` para los 3 parámetros de síntesis del motor neuronal Piper TTS:
- **`length_scale`** (Escala de Duración / Velocidad Base): Rango `0.20` a `3.00`, paso `0.05`.
- **`noise_scale`** (Expresividad Fonética): Rango `0.00` a `2.00`, paso `0.05`.
- **`noise_w_scale`** (Cadencia y Ritmo entre Pausas): Rango `0.00` a `2.00`, paso `0.05`.

Además, se expandió el catálogo de modelos de Piper con voces de alta resolución en español e inglés, y se integró persistencia completa en el almacenamiento de configuración con propagación en tiempo real.

---

## 2. Componentes Modificados y Creados

### Frontend & UI
- [frontend/widgets/no_wheel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/no_wheel.py): Añadido el componente `NoWheelDoubleSpinBox` para evitar alteraciones accidentales al hacer scroll con la rueda del ratón.
- [frontend/widgets/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/__init__.py): Exportación de `NoWheelDoubleSpinBox`.
- [frontend/dialogs/piper_voices_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_voices_dialog.py): 
  - Tarjeta de ajustes acústicos (`synthesis_card`) integrada en el diálogo de voces de Piper.
  - 3 SpinBoxes numéricos decimales con etiquetas explicativas y tooltips informativos.
  - Botón "Restablecer" para volver a los parámetros por defecto de fábrica.
  - Prueba de voz inmediata aplicando los parámetros actuales.

### Backend & Servicios
- [backend/providers/voices/tts_piper.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_piper.py):
  - Inclusión de `length_scale`, `noise_scale`, `noise_w_scale` en `PiperTTSProvider`.
  - Método `set_synthesis_params(length_scale, noise_scale, noise_w_scale)`.
  - Método `clear_cache()` para invalidar archivos temporales tras cambios acústicos.
  - **Capa de Normalización Automática de Configuración (`_prepare_compatible_config`)**: Corrige en tiempo de ejecución discrepancias de modelos comunitarios antiguos o experimentales (auto-cálculo de `num_symbols`, corrección de `phoneme_type: 'multilingual'` hacia `espeak`, inyección de claves de audio y espeak faltantes).
- [backend/services/chat/tts_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/tts_service.py):
  - Métodos `set_piper_synthesis_params` y `get_piper_synthesis_params` en `TTSManager`.
- [backend/services/chat/chat_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py):
  - Carga, inicialización y guardado persistente de las claves `piper_length_scale`, `piper_noise_scale`, `piper_noise_w_scale`.
- [backend/services/chat/piper_voice_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/piper_voice_manager.py):
  - Incorporación de modelos de otros distribuidores de Hugging Face en español:
    - **`es_ES-carlfm-high`** (Distribuidor: `friyin` - Alta Fidelidad 115 MB).
    - **`es_ES-glados-medium`** (Distribuidor: `csukuangfj` / `k2-fsa` - Voz temática).
  - Método `import_local_voice()` y detección dinámica de modelos personalizados en `get_installed_voices()`.
- [frontend/dialogs/piper_voices_dialog.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_voices_dialog.py):
  - Botón **"Importar Modelo ONNX"** para cargar cualquier modelo externo `.onnx` y `.onnx.json` con 1 clic.

### Internacionalización (i18n)
- [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) & [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json):
  - Nuevas cadenas de traducción completas sin textos hardcodeados ni fallbacks inline.

---

## 3. Pruebas y Validación
Se ejecutó la suite de pruebas unitarias [tests/test_piper_synthesis.py](file:///c:/Users/TheAn/Desktop/python/Kick/tests/test_piper_synthesis.py) mediante `pytest`:
- `test_nowheel_double_spinbox`: PASSED
- `test_piper_tts_provider_synthesis_params`: PASSED
- `test_chat_service_synthesis_persistence`: PASSED
- `test_piper_voices_dialog_instantiation`: PASSED
- `test_custom_voice_import`: PASSED
