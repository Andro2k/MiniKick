# Walkthrough: Evaluación y Benchmark de Motores TTS Locales (Piper TTS vs Kokoro-82M vs pyttsx3)

## 1. Resumen Ejecutivo de la Evaluación

Se implementó y ejecutó el sistema de benchmarking de síntesis de voz local en `tests/live/tts_benchmark_local.py`, integrado en el runner de pruebas `tests/run_tests.py`.

### Resultados del Benchmark en Vivo:

| Motor TTS | Modelo / Voz | Latencia (Frase Corta) | Latencia (Mensaje Chat) | Latencia (Sub Nivel 3) | RTF Promedio | Velocidad CPU | Calidad Auditiva |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **pyttsx3 (SAPI5)** | Windows Default | ~134.1 ms | ~147.1 ms | ~151.7 ms | 0.023 | **44.6x** | Robótica / Antigua |
| **Piper TTS** | `es_ES-davefx-medium` (ONNX) | **~187.5 ms** | **~310.5 ms** | **~409.3 ms** | **0.054** | **18.8x** | **Muy Natural, Fluida, Clara** |
| **Kokoro-82M** | `kokoro-v1.0.onnx` (`em_alex`) | ~1160.4 ms | ~2337.6 ms | ~3480.7 ms | 0.398 | **2.6x** | Estudio / Podcast |

---

## 2. Análisis Técnico y Recomendación Final

### 🏆 ¿Cuál te conviene más para que funcione de manera local y en CUALQUIER PC?

### **Ganador indiscutible: Piper TTS**

1. **Latencia casi instantánea para streaming en directo:**
   - Para un mensaje habitual de chat (~120 caracteres), **Piper TTS tarda solo 310 ms** en sintetizar y entregar el audio completo.
   - En cambio, **Kokoro-82M tarda ~2.3 segundos** en procesar el mismo mensaje en CPU. En un directo con chat activo, un retraso de más de 2 segundos por mensaje genera colas acumulativas y retrasos notorios en las alertas.

2. **Consumo de recursos y compatibilidad con PCs de gama baja:**
   - **Piper TTS**: Funciona a base de modelos ONNX ultraligeros de **~25 MB - 60 MB** optimizados para arquitecturas embebidas y CPUs básicas. No requiere GPU ni librerías pesadas, y corre a ~19x de velocidad real en CPU.
   - **Kokoro-82M**: El modelo ONNX pesa **~325 MB** y requiere matrices de cálculo más densas (StyleTTS2 de 82 millones de parámetros). En PCs sin GPU o con procesadores más modestos, el RTF puede acercarse a 1.0 (tiempo real justo) o provocar picos de CPU al streamer mientras juega.

3. **Madurez y Variedad de Acentos en Español:**
   - **Piper**: Cuenta con voces en español de España (`es_ES-davefx`, `es_ES-sharvard`, `es_ES-carlfm`), español de México (`es_MX-ald`, `es_MX-claude`) y otros dialectos completamente fonemizados y maduros.
   - **Kokoro-82M**: Su especialidad principal y mayor calidad está en inglés americano y británico; el soporte en español en v0.19/v1.0 aún es experimental.

---

## 3. Archivos y Muestras Generadas

- **Módulo de Benchmark**: `tests/live/tts_benchmark_local.py`
- **Suite Unitaria**: `tests/unit/test_tts_benchmark.py` (4 tests añadidos, 77/77 tests pasando).
- **Muestras de Audio `.wav` generadas**:
  - Carpeta: `tests/logs/tts_samples/`
  - `sample_piper_short_es.wav`
  - `sample_piper_medium_es.wav`
  - `sample_piper_long_es.wav`
  - `sample_kokoro-82m_short_es.wav`
  - `sample_kokoro-82m_medium_es.wav`
  - `sample_kokoro-82m_long_es.wav`
