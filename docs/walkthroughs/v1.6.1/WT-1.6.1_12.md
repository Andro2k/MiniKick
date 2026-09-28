# Walkthrough WT-1.6.1_12: Prevención de Auto-respuesta de Bots y Sincronización Inmediata de Comandos en Tabla

## Novedades
- **Supresión Universal de Comandos para Cuentas Bot**:
  - Incorporación de filtro de bloqueo para cuentas de bot (`@MiniKick`, `Nightbot`, `Botrix`, etc.) e insignias `bot` tanto en el pipeline de chat ([ChatController._step_commands](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py#L445)) como en el motor de comandos ([CommandService.process_incoming_message](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/commands_service.py#L180)).

## Mejoras
- **Sincronización Reactiva de Comandos del Sistema en Arranque**:
  - Emisión garantizada de `commands_changed` al concluir el registro inicial de plugins y comandos por defecto en `ChatController._register_system_commands()`.
  - Los controladores y vistas de interfaz (como `CommandsController` y `CommandView`) reciben la señal y reflejan de inmediato cualquier comando nuevo o actualizado sin necesidad de reiniciar la aplicación.
- **Eficiencia $\mathcal{O}(1)$ en Filtrado de Bots**:
  - Evaluación en tiempo constante $\mathcal{O}(1)$ mediante conjuntos inmutables (`frozenset`) y mapas hash para descartar mensajes de bots antes de ejecutar búsquedas de comandos o expresiones regulares.

## Correcciones
- **Eliminación del Bucle de Auto-respuesta en Kick (`INC-015`)**:
  - Se corrigió la incidencia donde los mensajes emitidos por el bot a través de la API de Kick eran recibidos de vuelta por WebSockets y evaluados como mensajes de usuario, activando comandos de regex (como `!discord`) cuando el bot listaba los comandos disponibles.
- **Visualización Inmediata en la Tabla de Comandos**:
  - Se corrigió la falta de actualización de la tabla en el primer inicio tras agregar un comando del sistema, asegurando que `!commands` aparezca visible en la interfaz desde el primer arranque.
