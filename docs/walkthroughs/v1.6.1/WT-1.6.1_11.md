# Walkthrough WT-1.6.1_11: Comando de Ayuda y Listado de Comandos del Chat con Partición Multimensaje

## Novedades
- **Comando de Consulta de Comandos (`!commands`, `!comandos`, `!help`, `!ayuda`)**:
  - Implementación del plugin nativo del sistema `[PLUGIN_CHAT_COMMANDS]` registrado de manera predeterminada para todos los usuarios con cooldown de 5 segundos.
  - Clasificación automática y dinámica de comandos en secciones temáticas:
    - `💬 Chat`: Comandos de texto regulares y utilidades de chat.
    - `🎵 Música`: Comandos multimedia vinculados al reproductor (`!sr`, `!song`, `!skip`, `!volume`, `!pause`, etc.).
    - `🎮 Widgets`: Comandos de interacción en pantalla (`!death`, `!score`, `!topchatters`, etc.).
    - `🛡️ Moderación`: Comandos reservados para moderadores y streamer (`!ttsmute`, `!ttsblock`, `!ttsunblock`, `!skiptts`).
  - **Filtros por categoría**: Permite al usuario consultar una categoría en particular (`!commands chat`, `!commands musica`, `!commands widgets`, `!commands mod`).
  - **Modo Estado Completo**: Mediante `!commands all` (o `!commands status`, `!commands todos`), muestra tanto los comandos habilitados (`✅`) como los deshabilitados (`❌`).

## Mejoras
- **Partición Inteligente Multimensaje para Kick y Twitch**:
  - Algoritmo de partición con límite seguro de 380 caracteres (`max_chars=380`), respetando los límites de longitud de carga útil de IRC en Twitch y de la API de Kick.
  - Envío secuencial y no bloqueante utilizando `QTimer.singleShot` con espaciado de 400ms para evitar bloqueos del bucle de eventos de la interfaz y prevenir penalizaciones por saturación o rate limit de las plataformas.
- **Seguridad y Privacidad de Roles**:
  - Los comandos de moderación solo se revelan si el emisor cuenta con las insignias `broadcaster` o `moderator`. Los viewers regulares reciben únicamente los comandos a los que tienen acceso real.
- **Eficiencia $\mathcal{O}(n)$**:
  - Clasificación en una única pasada sobre la colección de comandos y ordenamiento alfabético individual $\mathcal{O}(k \log k)$ por sección.
- **Internacionalización y Cero Hardcoded UI**:
  - Incorporación de todas las etiquetas de sección, prefijos de estado y textos de retroalimentación en `locales/es.json` y `locales/en.json` bajo la clave `chat.commands_help`.

## Correcciones
- **Prevención de Truncamiento en Plataformas de Streaming**:
  - Corrección de la pérdida de información cuando un canal cuenta con docenas de comandos activos, dividiendo ordenadamente las secciones o listas de comandos en mensajes correlativos.
