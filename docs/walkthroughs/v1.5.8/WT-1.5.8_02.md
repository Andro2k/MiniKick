# Walkthrough - WT-1.5.8_02: Sistema Integral de Alertas Multiplataforma (Kick & Twitch) y Overlays

**Versión:** `v1.5.8`  
**Documento:** `WT-1.5.8_02.md`  
**Fecha:** 02 de Septiembre, 2026  

---

## 1. Resumen Ejecutivo

Este documento consolida la arquitectura completa (Backend, Frontend, WebSocket y Overlays) del nuevo sistema de alertas en tiempo real de MiniKick para Kick y Twitch.
La solución permite detectar, encolar en $\mathcal{O}(1)$, personalizar visual y sonoramente, y proyectar hacia OBS eventos de:
- **Seguimientos (Follows)**: Detección instantánea en Kick mediante WebSocket Pusher (`GoalProgressUpdateEvent` + regex de bots de chat) y EventSub en Twitch (`channel.follow`).
- **Suscripciones y Resuscripciones**: Con niveles de suscripción e interpolación de variables.
- **Regalos de Suscripciones (Sub Bombs)**: Agrupamiento inteligente en cola para evitar saturación de pantalla.
- **Raids y Cheers/Bits**: Notificaciones dinámicas con lectura por voz (TTS).
- **Canjes de Puntos de Canal en Kick (0 ms)**: Migración de sondeo HTTP a eventos de WebSocket Pusher `RewardRedeemedEvent` en `chatroom_{chatroom_id}`.

---

## 2. Arquitectura de Datos y Backend (`backend/models/`, `backend/database/`, `backend/services/`)

### A. Capa de Dominio
- **`AlertType(str, Enum)`**: Tipos canónicos (`follow`, `subscription`, `resub`, `sub_gift`, `raid`, `cheer`).
- **`AlertEvent`**: Dataclass inmutable (`slots=True`, `frozen=True`) desacoplada de los esquemas específicos de Twitch y Kick.
- **`AlertConfig`**: Dataclass mutable que encapsula sonido, archivo multimedia (imagen o video transparente), plantilla de texto, duración en ms, volumen y lectura por TTS.

### B. Persistencia y Almacenamiento SQLite
- **Tabla `alert_configs`**: Clave primaria compuesta `(platform, alert_type)`.
- **Caché en Memoria $\mathcal{O}(1)$**: Acceso instantáneo en memoria sin consultas a disco durante transmisiones intensas.

### C. Cola $\mathcal{O}(1)$ y Agrupamiento de Regalos Masivos
- **`AlertQueue`**: Estructura FIFO basada en `collections.deque`.
- **Sub Bomb Consolidation**: Si un usuario regala varias suscripciones en una ventana corta de tiempo, la cola consolida los eventos en una sola alerta agregada (`amount = total`), impidiendo que OBS se bloquee con decenas de alertas redundantes.
- **Flujo de Confirmación Asíncrono (ACK)**: El overlay notifica `{"type": "alert_finished", "id": "..."}` al terminar la animación para solicitar el siguiente evento.

---

## 3. Protocolo WebSocket Pusher de Kick en Tiempo Real

Se analizaron e integraron los 4 tópicos en vivo de Kick:
1. `chatrooms.{chatroom_id}.v2`: Mensajes, encuestas y fijados.
2. `chatroom_{chatroom_id}`: Canjes de puntos de canal (`RewardRedeemedEvent`).
3. `channel_{channel_id}`: Eventos de canal (`GoalProgressUpdateEvent`, `FollowersUpdated`).
4. `channel.{channel_id}`: Tópico complementario.

Se erradicó por completo el antiguo hilo de sondeo HTTP (`RewardWorker`), reduciendo la latencia de 10 segundos a **0 ms** y ahorrando ~360 peticiones HTTP por hora.

---

## 4. Frontend: Interfaz de Configuración de Alertas (`frontend/views/alerts_view.py`)

- **`AlertEventCard`**:
  - Hereda de `ModernCard` con adherencia estricta al sistema de diseño sin estilos inline.
  - Botones temáticos con acento nativo: verde Kick (`role="action_kick"`) y púrpura Twitch (`role="action_twitch"`).
  - Distribución anti-cramping: Filas de sonido y video con anchos completos y explorador de archivos nativo.
  - Controles desacoplados: Duración (`NoWheelSpinBox`), Slider de Volumen (`NoWheelSlider`), switch TTS y botón de prueba.
- **`AlertsView`**:
  - Layout responsive de 2 columnas (`LeftToRight`) con cambio fluido a 1 columna vertical en ventanas estrechas (< 920px).
  - Selector de plataforma superior con chips de filtro temáticos.
  - Tarjeta de integración OBS con URL directa y botón de copiado en un clic (`QGuiApplication.clipboard`).

---

## 5. Plantilla de Overlay Web (`assets/overlays/alerts/alerts.html`)

- Estilizado Glassmorphism moderno con fuentes Google (`Outfit` e `Inter`).
- Soporte multimedia mixto (imágenes PNG/GIF y videos transparentes MP4/WebM).
- Reproductor de audio HTML5 con volumen calibrado.
- Barra de progreso temporal sincronizada y animaciones CSS fluidas con curvas cúbicas.

---

## 6. Verificación y Pruebas

- Pruebas dedicadas en `resources/tests/unit/ui/test_alerts_ui.py`, `test_alert_service.py`, `test_alert_storage.py` y `test_alert_models.py`.
- Cobertura 100% en simulación de eventos masivos, persistencia y despacho WebSocket.
