# Notas de la Versión — MiniKick v1.6.3

Fecha de Publicación: 10 de Octubre de 2026

La versión 1.6.3 de MiniKick se enfoca en reforzar la estabilidad global del sistema, elevar la seguridad en el almacenamiento de credenciales y maximizar el rendimiento del procesamiento de mensajes durante transmisiones de alta concurrencia. Esta actualización introduce cifrado transparente en reposo para los tokens de acceso, optimiza la fluidez de la interfaz limitando el consumo de recursos en ráfagas de chat, añade un mecanismo de recuperación de base de datos con respaldos automáticos fechados y garantiza la continuidad de las conexiones de chat y música incluso ante parpadeos de red o cancelaciones de canciones en reproducción.

---

## Novedades

A continuación se resumen las principales funcionalidades e innovaciones incorporadas en esta actualización:

| Sección | Característica | Descripción | Beneficio para el Usuario |
| --- | --- | --- | --- |
| Settings | Cifrado Seguro de Tokens de Autenticación | Almacenamiento cifrado en reposo para las credenciales de conexión de plataformas mediante los servicios de protección del sistema operativo. | Protege las claves de acceso y tokens de Kick y Twitch contra accesos no autorizados en el equipo local, garantizando la máxima seguridad de la cuenta. |
| Dashboard | Procesamiento Ultrafluido en Ráfagas de Chat | Agrupamiento inteligente del refresco visual en el panel de control y métricas en tiempo real. | Elimina la ralentización o congelamiento de la pantalla durante momentos de altísima actividad en el chat, manteniendo la interfaz ágil y respondiendo sin sobrecargar el equipo. |
| Settings | Recuperación Transparente de Base de Datos | Detección automática de anomalías con generación de copias de seguridad fechadas antes de reconstruir el almacenamiento. | Garantiza que ante un apagón repentino o falla en el disco, tus configuraciones se recuperen de forma segura sin perder jamás tus respaldos históricos. |
| Chat | Renovación Tolerante a Fallos de Red | Clasificación inteligente de errores al renovar los accesos de las plataformas interconectadas. | Previene la pérdida injustificada de la sesión de chat ante caídas breves de internet, evitando que tengas que volver a vincular tus cuentas durante el directo. |

> [!NOTE]
> Todos los mecanismos de cifrado y optimización de rendimiento operan de forma transparente e instantánea en segundo plano sin requerir ajustes adicionales por parte del streamer.

---

## Mejoras

* **Optimización en la Ruta de Mensajes y Filtros de Chat:**
Se implementó un sistema de almacenamiento temporal en memoria para la lista de usuarios y bots silenciados en el sintetizador de voz, así como para el filtrado anti-spam. Esto permite evaluar cientos de mensajes por segundo de forma instantánea sin realizar lecturas constantes al disco duro.
* **Cálculo Eficiente del Próximo Horario en la Agenda:**
La etiqueta del próximo evento o transmisión en el panel principal ahora memoriza su resultado y actualiza su cálculo en intervalos eficientes, evitando procesamientos repetitivos cada vez que llega un mensaje al chat.
* **Ajuste Dinámico del Nivel de Registros del Sistema:**
El registrador de eventos de la aplicación ajusta su intensidad por defecto para minimizar la escritura en disco durante las transmisiones, asegurando además que ante cualquier cierre inesperado el último evento del usuario quede guardado para diagnóstico.
* **Mayor Protección CSRF en la Vinculación de Cuentas:**
Se reforzó el flujo de inicio de sesión web exigiendo códigos de estado dinámicos e irrepetibles por cada intento de autenticación, asegurando que solo las solicitudes iniciadas directamente por el usuario sean aceptadas.
* **Aislamiento Seguro en el Servidor de Notificaciones y Alertas:**
El servidor interno de componentes visuales en pantalla restringe las conexiones exclusivamente al entorno local y valida de manera estricta el acceso a carpetas de archivos multimedia para prevenir la lectura no autorizada de archivos del sistema.
* **Reintento Inteligente ante Tiempos de Espera en Kick:**
Las solicitudes hacia la plataforma Kick detectan automáticamente pausas prolongadas de red o demoras en la respuesta, reintentando la conexión de forma limpia antes de reportar un fallo en la pantalla.
* **Gestión Silenciosa del Estado Offline en TikTok:**
Cuando la transmisión de TikTok no se encuentra activa, la aplicación ajusta la notificación a un aviso informativo sutil, evitando alertas de error innecesarias en la pantalla.

---

## Correcciones

* **Corrección de Cierre Inesperado en Tareas de Encuestas de Kick:**
Se solucionó la anomalía por la cual la sincronización de encuestas en Kick podía generar un cierre abrupto de la aplicación en segundo plano al detener el servicio o ejecutar acciones rápidas en el chat.
* **Corrección de Desincronización al Cambiar Canciones en YouTube:**
Se resolved el problema por el cual la cancelación o cambio de una canción en el reproductor de música continuaba emitiendo alertas o datos de la pista anterior debido a procesos que no detectaban a tiempo la orden de detención.
* **Corrección en la Sincronización al Silenciar Bots en el Chat:**
Se subsanó el fallo por el cual silenciar o desilenciar usuarios mediante los comandos del chat no actualizaba de inmediato la lista de exclusión en la voz interactiva hasta reiniciar el módulo.
* **Corrección en la Limpieza de Recursos del Servidor de Overlays:**
Se eliminaron falsas alarmas y advertencias de claves faltantes en el sistema de componentes visuales, asegurando una integración limpia con OBS Studio sin sobrecargar el registro de eventos.
* **Corrección en la Estabilidad de Conexiones de Base de Datos:**
Se corrigió el manejo de conexiones temporales para garantizar que la base de datos libere los archivos del sistema inmediatamente tras realizar comprobaciones o actualizaciones de esquema.