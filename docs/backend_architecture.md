# Arquitectura Técnica y Diagramas del Backend — MiniKick

Este documento detalla la arquitectura de software, los flujos de ejecución, los patrones de diseño y la complejidad algorítmica del backend de **MiniKick**.

---

## Índice de Contenidos
1. [Visión General y Principios de Diseño](#1-visión-general-y-principios-de-diseño)
2. [Diagrama 1: Arquitectura Global en Capas](#2-diagrama-1-arquitectura-global-en-capas)
3. [Diagrama 2: Pipeline de Ingesta y Procesamiento de Chat](#3-diagrama-2-pipeline-de-ingesta-y-procesamiento-de-chat)
4. [Diagrama 3: Motor de Resolución y Ejecución de Comandos](#4-diagrama-3-motor-de-resolución-y-ejecución-de-comandos)
5. [Diagrama 4: Sistema Autónomo de Timers](#5-diagrama-4-sistema-autónomo-de-timers)
6. [Diagrama 5: Motor de Síntesis de Voz (TTS)](#6-diagrama-5-motor-de-síntesis-de-voz-tts)
7. [Matriz de Complejidad Algorítmica (Big-O)](#7-matriz-de-complejidad-algorítmica-big-o)
8. [Referencias de Código y Módulos](#8-referencias-de-código-y-módulos)

---

## 1. Visión General y Principios de Diseño

El backend de MiniKick está estructurado siguiendo los principios de **Clean Architecture** y **Separación Estricta de Responsabilidades (SoR)**:

* **Desacoplamiento Reactivo**: Comunicación entre capas mediante el sistema de **Señales y Slots de Qt (`PySide6`)**, garantizando que los servicios de negocio desconozcan la implementación gráfica de la interfaz.
* **Aislamiento de Concurrencia**: Tareas intensivas de red y polling se ejecutan en hilos dedicados ([`QThread`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/)), manteniendo el bucle principal de la interfaz gráfica a 60 FPS sin bloqueos.
* **Fronteras Externas Protegidas**: Los WebSockets y APIs de terceros (Kick, Twitch, YouTube, TikTok) se adaptan en la capa de proveedores y se normalizan en objetos de transferencia ([`ChatMessageDTO`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/pipeline.py)) antes de ingresar a la lógica de dominio.
* **Eficiencia Algorítmica**: Uso intensivo de tablas de despacho $\mathcal{O}(1)$ para resolución de comandos, conjuntos nativos (`set`) para filtrado de palabras/bots, y buffers acotados (`deque(maxlen=N)`).

---

## 2. Diagrama 1: Arquitectura Global en Capas

El sistema se divide en seis capas horizontales bien delimitadas:

```mermaid
graph TD
    subgraph Presentation_Layer ["1. Capa de Presentación (UI & Overlays)"]
        UI_Chat["ChatView / ChatWidget"]
        UI_Cmd["CommandsView / Wizard"]
        UI_Timers["TimersView / Dialogs"]
        UI_Dash["DashboardView / Stats"]
        Overlay_Server["OverlayServer (FastAPI / WebSocket)"]
    end

    subgraph Controller_Layer ["2. Capa de Controladores (Qt Signals / Slots)"]
        Ctrl_Chat["ChatController"]
        Ctrl_Cmd["CommandController"]
        Ctrl_Timer["TimerController"]
        Ctrl_Dash["DashboardController"]
    end

    subgraph Service_Layer ["3. Capa de Dominio y Servicios de Negocio"]
        Svc_Pipe["MessagePipeline"]
        Svc_Chat["ChatService"]
        Svc_Cmd["CommandService (Dispatch Table O(1))"]
        Svc_Timer["TimerService (Interval & Line Tracker)"]
        Svc_Spam["SpamService (Anti-Flood & Repetition)"]
        Svc_TTS["TTSService & PiperVoiceManager"]
    end

    subgraph Handler_Layer ["4. Handlers Especializados"]
        Hnd_Filter["ChatFilterHandler (Banned Words / Bots)"]
        Hnd_Voice["TTSVoiceHandler (Role Badge Resolver)"]
        Hnd_Music["MusicCommandHandler (Plugin Bridge)"]
    end

    subgraph Worker_Layer ["5. Capa de Hilos en Segundo Plano (QThread)"]
        Wrk_KickChat["KickChatWorker"]
        Wrk_TwitchChat["TwitchChatWorker"]
        Wrk_YTChat["YouTubeChatWorker"]
        Wrk_TTChat["TikTokChatWorker"]
        Wrk_Timers["TimerWorker (Interval Poller)"]
        Wrk_Schedule["ScheduleWorker"]
    end

    subgraph Boundary_Layer ["6. Proveedores Externos & Persistencia"]
        Ext_KickWS["Kick WebSocket (Pusher)"]
        Ext_TwitchWS["Twitch IRC WebSocket"]
        Ext_YT["YouTube Live Client"]
        Ext_TT["TikTok Live Client"]
        Ext_KickAPI["Kick API Client"]
        Ext_TwitchAPI["Twitch Helix API"]
        DB_Storage["SQLite Storage (Commands, Timers, Settings)"]
    end

    %% Presentation to Controller
    UI_Chat <--> Ctrl_Chat
    UI_Cmd <--> Ctrl_Cmd
    UI_Timers <--> Ctrl_Timer
    UI_Dash <--> Ctrl_Dash

    %% Controller to Services & Handlers
    Ctrl_Chat --> Svc_Pipe
    Ctrl_Chat --> Svc_Chat
    Ctrl_Chat --> Svc_Cmd
    Ctrl_Chat --> Svc_Spam
    Ctrl_Chat --> Hnd_Filter
    Ctrl_Chat --> Hnd_Voice
    Ctrl_Cmd --> Svc_Cmd
    Ctrl_Timer --> Svc_Timer

    %% Services Interconnections
    Svc_Pipe --> Svc_Spam
    Svc_Pipe --> Svc_Cmd
    Svc_Pipe --> Svc_Chat
    Svc_Chat --> Svc_TTS
    Svc_Cmd --> Ext_KickAPI

    %% Workers to Controllers and Services
    Wrk_KickChat -.->|message_received| Ctrl_Chat
    Wrk_TwitchChat -.->|message_received| Ctrl_Chat
    Wrk_YTChat -.->|message_received| Ctrl_Chat
    Wrk_TTChat -.->|message_received| Ctrl_Chat
    Wrk_Timers -.->|post_message_requested| Svc_Cmd

    %% Workers to External Providers
    Wrk_KickChat --- Ext_KickWS
    Wrk_TwitchChat --- Ext_TwitchWS
    Wrk_YTChat --- Ext_YT
    Wrk_TTChat --- Ext_TT
    Wrk_Timers --- Ext_KickAPI

    %% Persistence connections
    Svc_Cmd --- DB_Storage
    Svc_Timer --- DB_Storage
    Svc_Chat --- DB_Storage
```

---

## 3. Diagrama 2: Pipeline de Ingesta y Procesamiento de Chat

Cuando un mensaje arriba desde cualquiera de las cuatro plataformas soportadas, fluye de forma estandarizada a través de un [`MessagePipeline`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/pipeline.py) modular:

```mermaid
sequenceDiagram
    autonumber
    participant WS as Proveedores Externos (Kick/Twitch/YT/TikTok)
    participant Worker as ChatWorker (QThread)
    participant Router as MainWindowCore._route_incoming_message
    participant Ctrl as ChatController.process_message
    participant Pipe as MessagePipeline
    participant Spam as SpamService (_step_spam)
    participant UI as Presentation / Overlays (_step_ui_render)
    participant Cmd as CommandService (_step_commands)
    participant TTS as TTS Engine (_step_tts)
    participant TimerSvc as TimerService

    WS->>Worker: Evento raw de mensaje de chat
    Worker->>Worker: Construye ChatMessageDTO estandarizado
    Worker-->>Router: emit message_received(dto)
    Router->>Router: Incrementa métricas de plataforma en Dashboard
    Router->>Ctrl: process_message(dto)

    Ctrl->>Pipe: execute(dto)
    
    rect rgb(240, 248, 255)
        Note over Pipe,Spam: Paso 1: Filtro Antispam
        Pipe->>Spam: _step_spam(dto)
        alt Es Spam (duplicado, repetición, flood)
            Spam-->>Ctrl: dto.is_cancelled = True
            Spam-->>Ctrl: emit spam_blocked()
            Note over Pipe: El pipeline se detiene inmediatamente (Break)
        end
    end

    rect rgb(245, 255, 245)
        Note over Pipe,UI: Paso 2: Renderizado UI & Overlays
        Pipe->>UI: _step_ui_render(dto)
        UI->>UI: Resuelve rol de usuario (_resolve_user_role)
        UI->>UI: Almacena en buffer local (deque maxlen=200)
        UI-->>Ctrl: emit message_received(para Overlays / WebSockets)
    end

    rect rgb(255, 250, 240)
        Note over Pipe,Cmd: Paso 3: Detección y Ejecución de Comandos
        Pipe->>Cmd: _step_commands(dto)
        alt Es Comando Válido
            Cmd->>Cmd: Ejecuta comando / activa Plugin
            Cmd-->>Ctrl: dto.is_command = True
            Cmd-->>Ctrl: emit command_executed()
        end
    end

    rect rgb(253, 245, 255)
        Note over Pipe,TTS: Paso 4: Síntesis de Voz (TTS)
        Pipe->>TTS: _step_tts(dto)
        alt TTS Activo y mensaje permitido
            TTS->>TTS: Limpia texto y censura palabras prohibidas
            TTS->>TTS: Resuelve voz según Badge de usuario
            TTS->>TTS: speak(texto, voice_id)
        end
    end

    opt Si dto.is_cancelled == False y plataforma es Kick/Twitch
        Ctrl->>TimerSvc: increment_chat_lines()
    end
```

### Flujo Lógico de Decisión en el Pipeline

```mermaid
flowchart TD
    Start(["Mensaje Recibido (ChatMessageDTO)"]) --> Step1{"¿Supera filtro de Spam?"}
    Step1 -- No (Detectado Spam) --> CancelDTO["Marcar dto.is_cancelled = True"] --> EmitSpam["Emitir señal spam_blocked"] --> EndDrop(["Fin: Mensaje Descartado"])
    Step1 -- Sí --> Step2["Paso UI: Renderizar en pantalla y enviar a Overlays"]
    Step2 --> Step3{"¿Es un comando del bot?"}
    Step3 -- Sí --> ExecCmd["Procesar en CommandService"]
    ExecCmd --> SetCmdFlag["Marcar dto.is_command = True"]
    Step3 -- No --> Step4
    SetCmdFlag --> Step4{"¿TTS habilitado y no es comando?"}
    Step4 -- Sí --> EvalTTS{"¿Pasa filtro de palabras y rol activo?"}
    EvalTTS -- Sí --> SpeakAudio["Sintetizar y reproducir Audio (TTS)"]
    EvalTTS -- No --> PostCheck
    Step4 -- No --> PostCheck
    SpeakAudio --> PostCheck{"¿Plataforma Kick o Twitch?"}
    PostCheck -- Sí --> IncLines["TimerService.increment_chat_lines()"] --> EndOk(["Fin: Procesado Exitosamente"])
    PostCheck -- No --> EndOk
```

---

## 4. Diagrama 3: Motor de Resolución y Ejecución de Comandos

El componente [`CommandService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/command_service.py) utiliza una tabla de despacho optimizada en memoria para resolver comandos en tiempo constante $\mathcal{O}(1)$:

```mermaid
flowchart TD
    MsgIn(["Mensaje Entrante: user, content, badges, platform"]) --> SplitText["Extraer primera palabra: first_word = parts[0].lower()"]
    
    SplitText --> LookupDispatch{"Buscar en _dispatch_table[first_word]"}
    
    LookupDispatch -- "Encontrado O(1)" --> MatchFound["Obtener definición del comando"]
    LookupDispatch -- "No encontrado" --> CheckRegex{"¿Existen comandos Regex activos?"}
    
    CheckRegex -- "Sí O(m)" --> IterateRegex["Evaluar patrones precompilados re.compile"]
    IterateRegex --> RegexMatch{"¿Coincidencia de patrón?"}
    RegexMatch -- Sí --> MatchFound
    RegexMatch -- No --> NotACommand(["No es comando (Continuar pipeline)"])
    CheckRegex -- No --> NotACommand

    MatchFound --> CheckPlatform{"¿Aplica a la plataforma actual? (Kick/Twitch/YT/TT)"}
    CheckPlatform -- No --> EndIgnored(["Fin: Ignorado por plataforma"])
    CheckPlatform -- Sí --> CheckPerms{"¿Tiene permisos suficientes?<br/>(everyone < sub < vip < mod < broadcaster)"}
    
    CheckPerms -- No --> EndPermDenied(["Fin: Permiso insuficiente"])
    CheckPerms -- Sí --> CheckCooldown{"¿Cooldown transcurrido?<br/>(now - last_executed >= cooldown)"}
    
    CheckCooldown -- No --> EndCooldown(["Fin: En enfriamiento"])
    CheckCooldown -- Sí --> RecordExecution["Actualizar cooldown_timers[trigger] = now<br/>Registrar log en SQLite"]
    
    RecordExecution --> InterpolateVars["Reemplazar macros:<br/>{user} -> Emisor<br/>{touser} -> Destinatario<br/>{random} -> 1 a 100"]
    
    InterpolateVars --> CheckPlugin{"¿Es comando de Plugin?<br/>([PLUGIN_CHAT_...], [PLUGIN_MUSIC_...])"}
    
    CheckPlugin -- "Plugin TTS / SysTTS" --> ExecPluginTTS["ChatController ejecuta acción interna de TTS"]
    CheckPlugin -- "Plugin Música" --> EmitMusicSignal["Emitir music_plugin_triggered"]
    CheckPlugin -- "Plugin Widget" --> EmitWidgetSignal["Emitir widget_plugin_triggered"]
    CheckPlugin -- "Texto Estándar" --> DispatchResponse["Despachar respuesta al chat"]

    DispatchResponse --> TargetPlat{"Plataforma de destino"}
    TargetPlat -- Kick --> KickSend["KickAPIClient.post_chat_message(...)"]
    TargetPlat -- Twitch --> TwitchSend["TwitchWorker.send_bot_message(...)"]
    TargetPlat -- YouTube / TikTok --> LogReadOnly["Registrar en log (Modo Read-Only)"]
```

---

## 5. Diagrama 4: Sistema Autónomo de Timers

El subsistema de temporizadores periódicos opera en un hilo separado ([`TimerWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/timers_worker.py)), asegurando que los mensajes periódicos se envíen en función tanto del **tiempo transcurrido** como de la **actividad real del chat (líneas mínimas)**:

```mermaid
stateDiagram-v2
    [*] --> ThreadStart: MainWindow inicia TimerWorker (QThread)
    
    state "Ciclo de Trabajo del TimerWorker" as WorkerLoop {
        ThreadStart --> SleepInterval: Espera check_interval (10 seg)
        SleepInterval --> PollStreamStatus: ¿Transcurrieron >= 60 seg?
        
        state PollStreamStatus {
            direction LR
            FetchAPI: KickAPIClient.fetch_stream_status(channel)
            UpdateStatus: Actualiza is_live, title, category
            FetchAPI --> UpdateStatus
        }
        
        PollStreamStatus --> CheckTimers: TimerService.check_timers(stream_status)
        
        state CheckTimers {
            direction TB
            EvalTimers: Iterar lista de Timers activos
            CheckLines: ¿chat_lines acumuladas >= min_lines requeridas?
            CheckInterval: ¿now - last_posted >= interval (online vs offline)?
            CheckFilters: ¿Coinciden keywords en título o categoría del stream?
            
            EvalTimers --> CheckLines
            CheckLines --> CheckInterval: Sí
            CheckInterval --> CheckFilters: Sí
            CheckFilters --> PrepareMessage: Coincide
        }
        
        CheckTimers --> DispatchSignal: Si hay mensajes listos
        
        state DispatchSignal {
            EmitSignal: emit post_message_requested(msg, apply_kick, apply_twitch)
            ResetState: chat_lines = 0, last_posted_time = now, rotar mensaje
            EmitSignal --> ResetState
        }
        
        DispatchSignal --> SleepInterval: Vuelve al reposo
    }
    
    DispatchSignal --> MainWindowRoute: MainWindow._send_timer_message
    MainWindowRoute --> CommandServicePost: CommandService.post_chat_message
    CommandServicePost --> KickDispatch: KickAPIClient.post_chat_message
    CommandServicePost --> TwitchDispatch: TwitchWorker.send_bot_message
```

### Lógica de Rotación Round-Robin de Mensajes en Timers

```mermaid
flowchart LR
    subgraph TimerState ["Estado del Temporizador en Memoria"]
        Index["message_index = 0"]
        List["messages = ['Mensaje A', 'Mensaje B', 'Mensaje C']"]
        Lines["chat_lines acumuladas"]
        Time["last_posted_time"]
    end

    Trigger(["Condiciones Cumplidas"]) --> Select["msg = messages[index % len(messages)]"]
    Select --> Dispatch(["Despachar a Kick / Twitch"])
    Dispatch --> IncIndex["message_index = (index + 1) % len(messages)"]
    Dispatch --> ResetLines["chat_lines = 0"]
    Dispatch --> UpdateTime["last_posted_time = now()"]
```

---

## 6. Diagrama 5: Motor de Síntesis de Voz (TTS)

El flujo de audio desacopla la recepción del texto de la síntesis acústica, con soporte para proveedores locales (Piper TTS) y remotos (Web/Edge TTS):

```mermaid
flowchart TD
    InputMsg(["Texto Cruto del Mensaje"]) --> FilterStep["ChatFilterHandler"]
    
    subgraph Sanitization ["1. Sanitización de Texto"]
        FilterStep --> RemoveEmotes["Remover identificadores de Emotes ([emote:id:name])"]
        RemoveEmotes --> StripURLs["Ocultar / resumir enlaces URL"]
        StripURLs --> CheckBannedWords{"¿Contiene palabras censuradas?"}
    end

    CheckBannedWords -- "Sí (Censurado)" --> DropTTS(["Descartar TTS"])
    CheckBannedWords -- "No (Limpio)" --> ResolveVoice["TTSVoiceHandler"]

    subgraph VoiceResolution ["2. Resolución de Voces por Rol"]
        ResolveVoice --> CheckRoles{"Determinar rol por insignias (Badges):<br/>1. Broadcaster<br/>2. Moderator<br/>3. VIP<br/>4. Subscriber<br/>5. Everyone"}
        CheckRoles --> LookupConfig["Obtener ID de voz configurado para el rol en SettingsStorage"]
    end

    LookupConfig --> CheckNamePrefix{"¿Opción 'Leer nombre' activada?"}
    CheckNamePrefix -- Sí --> FormatName["'Usuario dice: {mensaje}'"]
    CheckNamePrefix -- No --> FormatPure["'{mensaje}'"]

    FormatName --> TTSSvc["ChatService.speak(texto, voice_id)"]
    FormatPure --> TTSSvc

    subgraph Synthesis ["3. Síntesis y Reproducción"]
        TTSSvc --> ProviderSelect{"Proveedor activo"}
        ProviderSelect -- "Piper (Local ONNX)" --> PiperMgr["PiperVoiceManager (Subproceso / C++ runtime)"]
        ProviderSelect -- "Web / Cloud" --> WebMgr["WebTTSProvider (Async Stream)"]
        PiperMgr --> AudioOut["Reproductor de Audio (QAudioSink / Wave Player)"]
        WebMgr --> AudioOut
    end

    AudioOut --> Speaker(["Salida a Altavoces / Monitor de OBS"])
```

---

## 7. Matriz de Complejidad Algorítmica (Big-O)

| Operación | Componente / Método | Complejidad Temporal | Complejidad Espacial | Justificación Técnica |
| :--- | :--- | :---: | :---: | :--- |
| **Lookup de Comandos Directos** | [`CommandService.process_incoming_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/command_service.py) | $\mathcal{O}(1)$ | $\mathcal{O}(C)$ | Tabla hash (`_dispatch_table`) con claves pre-normalizadas para triggers y alias. |
| **Búsqueda de Comandos Regex** | `CommandService._regex_commands` | $\mathcal{O}(m)$ | $\mathcal{O}(m)$ | $m$ es el número de comandos regex activos. Patrones precompilados mediante `re.compile`. |
| **Verificación de Cooldowns** | `CommandService._try_execute` | $\mathcal{O}(1)$ | $\mathcal{O}(C)$ | Búsqueda por clave en diccionario `cooldown_timers[trigger]` comparando timestamps Unix. |
| **Evaluación de Permisos** | `CommandService._has_permission` | $\mathcal{O}(B)$ | $\mathcal{O}(1)$ | $B$ es la cantidad de badges del usuario ($\le 5$). Comparación numérica jerárquica directa. |
| **Pipeline de Mensajes** | [`MessagePipeline.execute`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/pipeline.py) | $\mathcal{O}(k)$ | $\mathcal{O}(1)$ | $k$ middlewares secuenciales registrados (spam $\to$ ui $\to$ commands $\to$ tts). Detención temprana con `is_cancelled`. |
| **Filtro de Palabras Prohibidas** | [`ChatFilterHandler.is_message_banned`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/handlers/chat_filter_handler.py) | $\mathcal{O}(W \cdot L)$ | $\mathcal{O}(W)$ | $W$ palabras censuradas contra longitud $L$ del mensaje. Uso de sets pre-hasheados. |
| **Chequeo de Timers Periódicos** | [`TimerService.check_timers`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/timer_service.py) | $\mathcal{O}(T)$ | $\mathcal{O}(T)$ | $T$ temporizadores activos. Evaluación unitaria de condiciones de línea y tiempo por ciclo. |
| **Incremento de Líneas de Chat** | `TimerService.increment_chat_lines` | $\mathcal{O}(T)$ | $\mathcal{O}(1)$ | Incremento directo de contadores enteros en el diccionario de seguimiento. |
| **Buffer de Historial de Chat** | `ChatController._message_buffer` | $\mathcal{O}(1)$ | $\mathcal{O}(M)$ | `collections.deque(maxlen=200)`. Inserción y desalojo de memoria en tiempo constante. |

*Donde $C$ = total de comandos, $m$ = comandos regex, $B$ = badges por usuario, $k$ = middlewares en pipeline, $W$ = palabras prohibidas, $L$ = longitud del mensaje, $T$ = temporizadores activos, $M$ = tamaño máximo del buffer de chat.*

---

## 8. Referencias de Código y Módulos

* **Controladores**:
  * [`ChatController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) — Orquestación del pipeline, eventos de chat, buffer UI y settings.
  * [`CommandController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/command_controller.py) — Interfaz de administración de comandos, wizards y validaciones.
  * [`TimerController`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/timer_controller.py) — Gestión y configuración de temporizadores y búsqueda de categorías.
* **Servicios de Dominio**:
  * [`MessagePipeline`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/pipeline.py) — Ejecución desacoplada de middlewares de mensajería.
  * [`CommandService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/command_service.py) — Motor de despacho de comandos, permisos, cooldowns y macros.
  * [`TimerService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/timer_service.py) — Lógica de activación periódica por tiempo, líneas de chat y filtros.
  * [`ChatService`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py) — Configuración de audio, volumen, velocidad y providers de voz.
* **Workers Concurrentes**:
  * [`TimerWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/timers_worker.py) — Hilo asíncrono para sondeo de estado de stream y disparo de timers.
  * [`KickChatWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/) — Conexión WebSocket Pusher hacia Kick.
  * [`TwitchChatWorker`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/) — Conexión WebSocket IRC hacia Twitch.
