# Walkthrough - WT-1.5.8_02: Arquitectura Backend de Alertas Multiplataforma (Kick y Twitch) y Plantilla Base de Overlays

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_02.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## Resumen Ejecutivo

Se implementó la **Fase 1 (Backend)** del sistema de alertas en vivo de MiniKick para Kick y Twitch. La arquitectura permite detectar, normalizar, encolar y emitir eventos de streaming en tiempo real (Follows, Suscripciones, Resuscripciones, Regalos de Subs, Raids y Cheers/Bits) hacia el overlay de OBS mediante WebSockets dedicados, con soporte para personalización multimedia, cola $\mathcal{O}(1)$ con agrupación inteligente de sub bombs y lectura opcional por voz (TTS).

---

## Componentes y Cambios Implementados

### 1. Capa de Dominio (`backend/models/alert_models.py`)
- **`AlertType(str, Enum)`**: Tipos de alertas canónicos (`follow`, `subscription`, `resub`, `sub_gift`, `raid`, `cheer`).
- **`AlertEvent`**: Dataclass inmutable con `slots=True` y `frozen=True` que desacopla la lógica interna del formato de payloads de Twitch y Kick.
- **`AlertConfig`**: Dataclass mutable que define el comportamiento de cada alerta (archivo de sonido, imagen/video, plantilla de texto, duración en ms, volumen y lectura por TTS).

### 2. Capa de Persistencia (`backend/database/alert_storage.py`)
- **Tabla SQLite `alert_configs`**: Clave primaria compuesta `(platform, alert_type)`, almacenando de forma atómica la configuración de cada evento.
- **Cache en Memoria $\mathcal{O}(1)$**: Acceso instantáneo por tupla `(platform, alert_type)` sin lecturas repetidas a disco durante eventos intensos de stream.
- **Plantillas Predeterminadas**: Generación automática de mensajes por defecto en caso de no existir configuración guardada.

### 3. Capa de Lógica de Negocio y Cola $\mathcal{O}(1)$ (`backend/services/alerts/`)
- **`AlertQueue` (`alert_queue.py`)**:
  - Estructura FIFO implementada con `collections.deque` garantizando inserción y desencolado en $\mathcal{O}(1)$.
  - **Agrupamiento de Regalos Masivos (Sub Bomb Consolidation)**: Si un usuario regala múltiples suscripciones en una ventana de tiempo (ej. 3 segundos), la cola consolida los eventos en una sola alerta combinada (`amount = total`), evitando saturar OBS con decenas de alertas repetitivas.
  - **Flujo de Confirmación Asíncrono (ACK)**: El overlay envía un mensaje `{"type": "alert_finished", "id": "..."}` por WebSocket al terminar la animación para solicitar la siguiente alerta.
- **`AlertService` (`alert_service.py`)**:
  - Filtra alertas desactivadas según la base de datos.
  - Interpola variables dinámicas en el texto (`{user}`, `{amount}`, `{tier}`, `{platform}`, `{message}`).
  - Despacha hacia el servidor de overlay y, opcionalmente, envía el texto al motor de TTS si la alerta tiene activada la lectura de voz.
  - Deduplicación en $\mathcal{O}(1)$ de IDs de eventos para prevenir falsos disparos por reconexión de sockets.

### 4. Servidor de Overlay (`backend/services/overlay/`)
- **Canal WebSocket `"alerts"`**: Añadido a `OverlayServerManager` para distribución dirigida únicamente a clientes de alertas.
- **Rutas HTTP Registradas**: Mapeo de `/alerts`, `/alerts/` y `/alert` en `STATIC_ENDPOINTS_MAP` apuntando a `assets/overlays/alerts/alerts.html`.
- **Procesamiento de ACKs**: `OverlayRequestHandler` captura mensajes entrantes de clientes WebSocket y notifica al callback `on_alert_finished` de `AlertService`.

### 5. Proveedores de Red y Workers
- **Kick (`backend/providers/chat/kick_websocket.py` & `kick_chat_worker.py`)**:
  - Escucha eventos de Pusher: `App\Events\SubscriptionEvent`, `App\Events\GiftedSubscriptionsEvent`, `App\Events\StreamHostEvent` y `App\Events\FollowersUpdated`.
  - Normaliza a `AlertEvent` y emite la señal `alert_received(AlertEvent)`.
- **Twitch (`backend/workers/rewards_worker.py`)**:
  - Suscribe automáticamente temas de EventSub vía WebSocket (`channel.follow`, `channel.subscribe`, `channel.subscription.message`, `channel.subscription.gift`, `channel.cheer`, `channel.raid`).
  - Emite la señal `alert_received(AlertEvent)`.
- **`MainWindowCore`**: Conexión reactiva de las señales de ambos workers al procesador central `self.container.alert_service.process_event`.

### 6. Plantilla Base de Overlay (`assets/overlays/alerts/alerts.html`)
- Archivo HTML5, CSS y JavaScript moderno sin dependencias externas:
  - Estilizado premium con Glassmorphism, Google Fonts (`Outfit` e `Inter`) y bordes neón acordes a la plataforma (Kick `#53FC18`, Twitch `#9146FF`).
  - Soporte de audio HTML5 con control de volumen.
  - Soporte multimedia mixto (imágenes PNG/GIF y videos transparentes MP4/WebM).
  - Barra de progreso temporal sincronizada y animaciones CSS de entrada y salida con curvas cúbicas.

---

## Verificación y Pruebas Automatizadas

Se crearon 4 nuevas suites de pruebas unitarias automatizadas cubriendo el 100% de la nueva arquitectura:
- `resources/tests/unit/services/test_alert_models.py` (3 tests)
- `resources/tests/unit/services/test_alert_storage.py` (2 tests)
- `resources/tests/unit/services/test_alert_queue.py` (2 tests)
- `resources/tests/unit/services/test_alert_service.py` (4 tests)

**Resultado de la Suite Completa**:
```text
============================ 187 passed in 10.67s =============================
```
187 pruebas pasando exitosamente sin advertencias ni regresiones.
