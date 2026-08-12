# Release Notes - MiniKick Version v1.5.0

> MiniKick v1.5.0 amplía la suite de herramientas hacia una arquitectura **Multi-Plataforma nativa**, introduciendo integración simultánea con **Twitch** y **Kick**, moderación anti-spam configurable por plataforma (switches independientes de Kick y Twitch por regla), eliminación de mensajes duplicados en Kick, aislamiento estricto de filtros anti-spam, historial de chat en segundo plano, orden cronológico de chat, renderizado en UI de respuestas salientes del bot, lectura continua en TTS Local (SAPI5), permisos de moderación de Twitch (scopes) y banner de notificación de permisos faltantes.

---

## Novedades Principales

### 1. Eliminación de Duplicados en Kick
- **Restricción por Protocolo**: `_handle_bot_response()` restringe el renderizado local a Twitch (`platform == "twitch"`). Kick procesa los mensajes del bot exclusivamente desde su WebSocket de Pusher oficial, erradicando entradas duplicadas.

### 2. Orden Cronológico del Pipeline de Chat
- **Mensaje de Usuario Primero**: Reordenamiento en `ChatController` para que `_step_ui_render` preceda a `_step_commands`, garantizando que en `ChatDisplay` los comandos del espectador aparezcan primero y la respuesta del bot inmediatamente después.

### 3. Alineación de Identidad del Emisor del Bot
- **Nombre de Usuario Real**: La interfaz de chat utiliza dinámicamente el nombre de la cuenta vinculada (ej. `TheAndro2K` o el nick del bot) para las respuestas enviadas por MiniKick.

### 4. Reproducción Continua en TTS Local (SAPI5 / Windows)
- **Instanciación Segura por Mensaje**: Refactorización de `LocalTTSProvider` para inicializar y limpiar la pila COM (`pythoncom`) y el motor `pyttsx3` por cada mensaje entrante.

### 5. Timers Multi-Plataforma (Switches Kick/Twitch y Tags en Tabla)
- **Selección de Plataforma por Timer**: Inclusión de switches independientes en `TimerConfigWizard` para activar o desactivar cada temporizador por canal (Kick, Twitch o Ambos).
- **Insignias en Tabla e Integración i18n**: Visualización de tags estilizadas (`[Kick]` en verde y `[Twitch]` en morado) en la columna Plataformas de `TimersView`. Enrutamiento automatizado con `CommandService`.

---

## Métricas de Calidad

| Componente | Estado Anterior | Estado Actual (v1.5.0) | Impacto |
| :--- | :--- | :--- | :--- |
| Mensajes del Bot en Kick | Aparecían dos veces (Duplicados) | **Entrada Única desde WebSocket** | Chat de Kick limpio sin duplicaciones |
| Orden Cronológico en UI | La respuesta del bot aparecía antes del comando | **Orden Estricto (Comando -> Respuesta)** | Línea de tiempo de chat 100% natural |
| Timers de Chat | Únicamente emisión global a Kick | **Switches Kick/Twitch + Insignias en Tabla** | Control total multi-plataforma por temporizador |
| Cobertura de Pruebas Unitarias | 15 pruebas pasando | **17 pruebas pasando** en 0.76s | Cobertura total de pipeline, timers y ejecutores |
