# Walkthrough Técnico — MiniKick v1.6.8 (Paso 21)

Seguimiento de las miniaturas de recompensas: el `minikick.log` del usuario muestra que las imágenes se regeneran (15/46) pero ningún `.mp4` produce fotograma.

---

## Correcciones

- **Captura de video con salida de audio silenciada:** `ThumbnailService` usa ahora un `QAudioOutput` a volumen 0, igual que el reproductor que sí funciona en la app (`DraggableBox`). Es una hipótesis: en Windows el backend FFmpeg de Qt puede no entregar fotogramas a un `QMediaPlayer` sin salida de audio.
- **Diagnóstico en el log:** cuando no hay fotograma, el `warning` incluye ahora el estado del medio y el mensaje de error de Qt (`status=…, error=…`). Qt multimedia está silenciado por `QT_LOGGING_RULES`, por lo que antes no quedaba rastro de la causa.
- **Temporizador propio:** se reemplaza `QTimer.singleShot` (que dejaba temporizadores colgados tras cada captura) por un `QTimer` local que se detiene al terminar.

## Mejoras

- **Capas / cohesión:** la captura se extrae a `_capture_video_frame` y la codificación a `_encode_png`; `generate_media_thumbnail` solo decide por tipo de archivo.

## Archivos afectados

| Capa | Archivo |
| --- | --- |
| Servicio | `backend/services/rewards/thumbnail_service.py` |

## Verificación

- mp4 H.264+AAC de prueba: miniatura generada (3137 bytes) en 0.01 s tras la primera carga.
- Archivo `.mp4` inválido: devuelve `None` sin bloquear y registra `status=InvalidMedia, error=Could not open file`.
- El contenedor no tiene dispositivo de audio (`QAudioOutput` falla al crearse), por lo que esas pruebas usaron un doble para el audio. **Pendiente en Windows:** confirmar que los videos generan miniatura; si no, el nuevo `warning` indicará la causa.
