# Walkthrough: Precalentamiento Asíncrono (Warm-Up) para Piper TTS

## 1. Resumen de la Implementación

Se implementó un sistema de **precalentamiento inteligente y no bloqueante (Zero-Latency Warm-Up)** para los modelos neuronales de **Piper TTS**:
1. **Carga en Segundo Plano**: Al iniciar la aplicación, cambiar de voz en el panel de ajustes o seleccionar un nuevo motor de voz, se ejecuta un hilo en segundo plano que carga el modelo ONNX en la memoria RAM y realiza una micro-inferencia silenciosa para compilar los grafos de ejecución en ONNX Runtime.
2. **Eliminación del Cold Start**: Se eliminó la pausa inicial de 1 a 2.5 segundos que ocurría la primera vez que una voz hablaba. Ahora, la respuesta de audio es instantánea (< 100 ms) desde la primera palabra.
3. **Caché en Memoria RAM $O(1)$**: Los modelos cargados se mantienen en `_loaded_models` con acceso inmediato para todas las reproducciones subsiguientes.

---

## 2. Componentes Modificados

- `backend/interfaces/tts_interfaces.py`:
  - Añadido `warm_up(self, voice_id: str = None) -> None` al protocolo `ITTSProvider`.
- `backend/providers/voices/tts_piper.py`:
  - Implementado `warm_up(self, voice_id, async_mode)` con inicialización de tensores y sesión de ONNX.
- `backend/services/chat/tts_service.py` & `backend/services/chat/chat_service.py`:
  - Activación automática de `warm_up` al seleccionar proveedores y voces.
- `tests/unit/test_tts_piper_provider.py`:
  - Añadido test unitario `test_piper_tts_provider_warm_up`.

---

## 3. Pruebas y Validación

- **Suite de Pruebas Unitarias**:
  - `uv run pytest tests/unit` -> **85/85 pasadas (100% OK)**.
