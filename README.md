---
description: El centro de control definitivo, modular y ligero para streamers en Kick.com
---

# MiniKick

[![Latest Release](https://img.shields.io/github/v/release/Andro2k/MiniKick?style=for-the-badge\&logo=kick\&color=10BB10\&labelColor=191919)](https://github.com/Andro2k/MiniKick/releases/latest) [![Windows Support](https://img.shields.io/badge/Plataforma-Windows-0078D6?style=for-the-badge\&logo=windows\&logoColor=white\&labelColor=191919)](https://github.com/Andro2k/MiniKick/releases/latest) [![Python Version](https://img.shields.io/badge/Python-3.14.5-3776AB?style=for-the-badge\&logo=python\&logoColor=white\&labelColor=191919)](https://www.python.org/) [![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?style=for-the-badge\&logo=qt\&logoColor=white\&labelColor=191919)](https://doc.qt.io/qtforpython-6/) [![Clean Architecture](https://img.shields.io/badge/Arquitectura-Clean_Code-FFb900?style=for-the-badge\&logo=dataiku\&logoColor=white\&labelColor=191919)](./#arquitectura-e-ingenieria) [![License](https://img.shields.io/github/license/Andro2k/MiniKick?style=for-the-badge\&color=blue\&labelColor=191919)](https://github.com/Andro2k/MiniKick/blob/main/LICENSE/README.md)<br>

MiniKick es una aplicación de escritorio nativa diseñada para orquestar la interacción en directo sin sacrificar los FPS de tu transmisión. Operando por completo fuera del navegador, reduce drásticamente el consumo de memoria RAM y ciclos de CPU, integrando lectura de chat inteligente por voz (TTS), moderación automatizada, control multimedia en tiempo real y un potente sistema de overlays personalizables para OBS.<br>

[![Descargar Última Versión](https://img.shields.io/badge/DESCARGAR_ULTIMA_VERSION-10BB10?style=for-the-badge\&logo=windows\&logoColor=white)](https://github.com/Andro2k/MiniKick/releases/latest)

***

### Vista Previa de la Interfaz

![MiniKick Dashboard - Panel General de Control](.gitbook/assets/dashboard_preview.png)

![Ajustes de Voz, Roles y Moderacion de Chat](.gitbook/assets/chat_settings_preview.png)

![Reproductor de Musica y Cola de Reproduccion](.gitbook/assets/music_player_preview.png)

![Lienzo de Overlay de Chat para OBS y Temas Visuales](.gitbook/assets/chat_overlay_preview.png)

***

### Funcionalidades Principales

| Módulo                     | Función                     | Descripción                                                                                                                                                      |
| -------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Motor de Chat**          | Pipeline Unidireccional     | Procesamiento de mensajes mediante tubería de interceptores puros (_AutoMod -> Comandos -> UI -> TTS_) con visualización de comandos en el historial de sala.    |
| **Lienzo y Overlays**      | OBS Widgets                 | Generación local de overlays de chat de alto rendimiento con soporte de emotes Kick y 7TV, auto-ocultación, marcas de tiempo y redimensionamiento dinámico.      |
| **Voz Híbrida (TTS)**      | Narración Inteligente       | Voces personalizadas por roles (Streamer, Moderador, VIP, Suscriptor). Alternancia dinámica entre voces de Microsoft Edge-TTS y SAPI5 local.                     |
| **Integración de Música**  | Control de Puntos           | Soporte de Spotify y YouTube Music. Canje de canciones (`!sr`), saltos (`!skip`) y consulta de pista (`!song`) con portadas dinámicas y progreso en tiempo real. |
| **AutoMod Integrado**      | Filtros Anti-Spam           | Protección activa contra exceso de mayúsculas, símbolos, repeticiones, enlaces y párrafos masivos con bloqueo visual de controles en caso de fallos.             |
| **Diagnóstico y Reportes** | Herramientas de Estabilidad | Captura global de excepciones con reporte de crashes automatizado a webhooks de Discord y separador de lógica visual en informes de bugs.                        |

> \[!NOTE] Todas las preferencias de usuario, bases de datos locales (`SQLite`) y tokens cifrados de sesión persisten de forma aislada en el directorio nativo del sistema: `AppData\Local\.Minikick`.

***

### Arquitectura e Ingeniería

MiniKick está construido bajo estándares estrictos de **Ingeniería de Software a Escala**, priorizando la **Separación de Responsabilidades (SoR)**, **Inversión de Dependencias (IoC)** y **Eficiencia Algorítmica Big-O**.

```mermaid
flowchart TD
    subgraph SOURCELAYER["1. Plataformas Externas (Ingestión de Datos)"]
        KICK_EXT["Kick (Pusher WebSocket)"]
        TWITCH_EXT["Twitch (IRC WebSocket)"]
        YT_EXT["YouTube Live (Polling pytchat)"]
    end

    subgraph WORKERS["2. Hilos de Conexión en Paralelo (QThread)"]
        K_WORKER["ChatWorker\n(Pusher Protocol)"]
        T_WORKER["TwitchChatWorker\n(IRC Protocol + Ping/Pong)"]
        Y_WORKER["YouTubeChatWorker\n(Deduplicación & Polling)"]
    end

    subgraph CORE_ORCH["3. Orquestador Central (MainWindowCore)"]
        ROUTE["_route_incoming_message(dto)\nNormaliza a ChatMessageDTO"]
    end

    subgraph PIPELINE["4. Pipeline de Procesamiento de Mensajes (MessagePipeline)"]
        STEP_SPAM["1. SpamService\n• Filtro Mayúsculas\n• Párrafos / Símbolos\n• Emotes ignorados en O(1)"]
        STEP_UI["2. Dispatch a UI\n• Emisión de señal Qt\n• Ring Buffer deque(maxlen=200)"]
        STEP_CMD["3. CommandService\n• Regex & Prefijos\n• Cooldowns O(1)\n• Permisos de Rol\n• Detección de Plugins"]
        STEP_TTS["4. TTS Pipeline\n• Filtro de roles y bots\n• Normalización de texto"]
    end

    subgraph ENGINES["5. Servicios y Motores de Ejecución"]
        MUSIC_SRV["YouTubeMusicProvider\n• Resuelve URLs (yt-dlp)\n• Cache en disco O(1)\n• Reproductor QMediaPlayer"]
        TTS_MGR["TTSManager (2 Threads)\n• Downloader Worker\n• Synthesis Worker\n• Piper ONNX / Local SAPI / Web"]
        OVERLAY_SRV["OverlayServerManager (Puerto 8090)\n• Servidor HTTP + WebSockets\n• Envío a OBS (Chat, Widgets, Music)"]
        SCHED_SRV["ScheduleService / Worker\n• Actualización automática\n• Categorías y Títulos"]
        TIMER_SRV["TimerWorker\n• Notificaciones periódicas"]
    end

    subgraph DATABASE["6. Capa de Persistencia (SQLite en Modo WAL)"]
        DB["DatabaseManager\nPRAGMA journal_mode=WAL\nPRAGMA busy_timeout=5000"]
        T_TOKENS[("Tokens & OAuth")]
        T_SETTINGS[("Ajustes Generales")]
        T_COMMANDS[("Comandos y Alias")]
        T_SPAM[("Filtros y Banned Words")]
        T_TIMERS[("Timers y Programación")]
        T_MUSIC[("Historial de Música")]
    end

    KICK_EXT --> K_WORKER
    TWITCH_EXT --> T_WORKER
    YT_EXT --> Y_WORKER

    K_WORKER --> ROUTE
    T_WORKER --> ROUTE
    Y_WORKER --> ROUTE

    ROUTE --> STEP_SPAM
    STEP_SPAM --> STEP_UI
    STEP_UI --> STEP_CMD
    STEP_CMD --> STEP_TTS

    STEP_CMD -->|"!sr o comandos de música"| MUSIC_SRV
    STEP_CMD -->|"[PLUGIN_WIDGET]"| OVERLAY_SRV
    STEP_TTS --> TTS_MGR

    PIPELINE <--> DATABASE
    MUSIC_SRV <--> DATABASE
    SCHED_SRV <--> DATABASE
    TIMER_SRV <--> DATABASE
```

#### Principios Clave de Diseño:

1. **Aceleración JSON en C/Rust (`msgspec` / `orjson`):** Deserialización de alta velocidad con fallback transparente a la librería estándar, reduciendo el consumo de CPU por mensaje en un ~60%.
2. **Eficiencia Algorítmica $\mathcal{O}(1)$:** Erradicación de bucles anidados en rutas críticas. Desalojo de historiales mediante colas de doble extremo `collections.deque` en `SpamService`, `RewardWorker` y `LogService`.
3. **Carga Perezosa (Lazy Loading):** Los módulos secundarios, workers de descarga y librerías externas pesadas se cargan bajo demanda, logrando un arranque en frío **~50% más rápido** (de 4.17 s a 2.13 s).
4. **Patrón Pipeline (Chain of Responsibility):** Desacoplamiento total del procesamiento de mensajes. Cada mensaje es un `ChatMessageDTO` inmutable que atraviesa etapas independientes de sanitización, filtrado y despacho.
5. **Gestión Segura de Memoria y Concurrencia:** Hilos secundarios aislados en `QThread` con señales/ranuras Qt (`Signals/Slots`), bloqueos atómicos (`threading.Lock`) y limpieza determinista de recursos.

> \[!IMPORTANT] **Normativa de Contribución:** Cualquier propuesta de cambio para el proyecto debe pasar auditoría de complejidad temporal y respetar el desacoplamiento de capas para ser integrada en la rama principal.

***

### Stack Tecnológico

* **Core & GUI:** Python 3.14.5 | PySide6 (Qt for Python) | Qt Style Sheets (QSS contextual)
* **Servicios de Red:** HTTP Server Local | WebSockets | Requests | Cloudscraper (Bypass de Cloudflare)
* **Motores de Voz:** Edge-TTS (Edge Cloud) | Pyttsx3 (SAPI5 local de Windows)
* **Motores de Audio:** YT-DLP (YouTube resolve) | Spotify Web API
* **Base de Datos y Almacenamiento:** SQLite3 | JSON File Storage
* **Compilación y Empaquetado:** PyInstaller | Inno Setup

***

### Guía de Despliegue

#### Entorno de Producción (Creadores)

1. Dirígete a la sección de [Releases Oficiales](https://github.com/Andro2k/MiniKick/releases/latest).
2. Descarga la versión más reciente (`MiniKick.exe` o el instalador ejecutable).
3. Ejecuta la aplicación en Windows 10/11 sin configuraciones adicionales.

#### Entorno de Desarrollo (Ingenieros)

Configuración del entorno local utilizando `uv`:

```bash
# 1. Clonar el repositorio
git clone https://github.com/Andro2k/MiniKick.git
cd MiniKick

# 2. Sincronizar el entorno virtual y dependencias con uv
uv sync

# 3. Ejecutar la aplicación
uv run python main.py

# 4. Compilar ejecutable de producción
uv run pyinstaller --clean --noconfirm MiniKick.spec
```

> \[!TIP] Si experimentas algún comportamiento inesperado de red o cierre abrupto, revisa la pestaña interna **Developer -> Logs** de la aplicación o consulta el diálogo de reporte de fallos automatizado antes de abrir un ticket de soporte.

<sub>Diseñado y desarrollado con estándares de arquitectura por</sub> [<sub>**TheAndro2K**</sub>](https://github.com/Andro2k) <sub>• Distribuido bajo la Licencia MIT</sub>
