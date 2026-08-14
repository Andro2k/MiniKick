# Walkthrough - WT-1.5.0_07: Corrección de Cambio Dinámico y Detección Caliente (Hot-Plug) de Dispositivos de Audio

## Resumen de Cambios

1. **Corrección de Método en PySide6 (`AttributeError`)**:
   - Se identificó que `QAudioOutput` en PySide6 utiliza el método `.setDevice(QAudioDevice)` y no `.setAudioDevice(...)`.
   - Se corrigió en [`youtube_client.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/music/youtube_client.py) y en [`tts_online.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/voices/tts_online.py).
   - Esto resuelve la imposibilidad de cambiar el dispositivo de audio mientras sonaba la música o la voz, aplicando el cambio de salida de forma inmediata e instantánea.

2. **Detección Caliente (Hot-Plug) de Nuevos Dispositivos**:
   - En [`settings_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/settings_view.py), se conectó la señal nativa `QMediaDevices.audioOutputsChanged`.
   - Cuando el usuario conecta o desconecta un dispositivo de audio (auriculares USB, altavoces, cable virtual, etc.) con MiniKick abierto, la lista de dispositivos desplegable se repobla automáticamente preservando la selección actual.

---

## Verificación

- **Pruebas Automatizadas (`pytest`)**: Ejecutado correctamente con 35 pruebas aprobadas.
- **Cambio en Vivo**: Al seleccionar un nuevo dispositivo de salida durante la reproducción, el sonido se desvía inmediatamente al nuevo dispositivo.
- **Hot-Plug**: Al conectar un nuevo periférico de audio, la lista en Ajustes se actualiza al instante.
