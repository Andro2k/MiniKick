---
id: WT-1.4.0-01
feature: Live Chat Improvements
date: 2026-07-09
components: [chat_view.py, chat_controller.py, chat_service.py, tts_service.py, theme.py, blocks_component.py, main_window_core.py, pipeline.py]
description: Added a tabbed UI to the live chat containing general voice configurations, custom voice selectors per role, and a muted users manager. Implemented local message timestamp rendering and flex/scroll layout enhancements to avoid content clipping on resize.
---

# Resumen de Cambios (Walkthrough) - Mejoras del Chat

Se han completado todas las modificaciones necesarias en el chat en vivo según el plan de implementación aprobado. A continuación se detallan los cambios realizados y los resultados de las pruebas.

## Cambios Realizados

### 1. Interfaz de Usuario y Pestañas en la Vista de Chat
- Se rediseñó el panel izquierdo de la vista de chat en [chat_view.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/chat_view.py) para utilizar un `QTabWidget` con dos pestañas principales:
  - **Ajustes de Voz**: Unifica en un único panel desplazable (`QScrollArea`) tanto la configuración de voz general como la asignación de voces personalizadas por roles (Streamer, Moderador, VIP, Suscriptor). Se separan de manera elegante usando una etiqueta de categoría (`QLabel[role="category"]`) y una línea divisora (`QFrame[role="divider"]`).
  - **Silenciados**: Pestaña dedicada a la administración de usuarios silenciados mediante `BotMutePanel`.
- Se aplicó un comportamiento flexible a la UI para evitar recortes de texto y desbordamiento en anchos reducidos, y optimizar el comportamiento al maximizar la ventana:
  - Se configuró el combo box del motor de voz (`combo_voice`) con un ancho mínimo de `80px` y una política de tamaño expansiva (`QSizePolicy.Policy.Expanding`), permitiendo que se encoja correctamente en anchos reducidos y se estire ocupando todo el ancho libre disponible al maximizar la pantalla.
  - Se estableció un ancho fijo equilibrado de `140px` en los combo boxes de roles del chat, lo que garantiza su correcta visibilidad y un espacio óptimo de visualización.
  - Se habilitó el auto-ajuste de línea (`setWordWrap(True)`) en los títulos y descripciones de las filas (`SettingRow`) en [blocks_component.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/blocks_component.py) para que el texto de la izquierda fluya hacia abajo.
  - Se agregó un espaciador flexible (`addStretch()`) al final de `config_card` para absorber todo el espacio vertical sobrante al redimensionar/maximizar la ventana, evitando que se abran espacios indeseados entre los textos y alineando de forma correcta los iconos de las filas.
- Siguiendo los principios de diseño del proyecto, no se utiliza `setStyleSheet` inline; en su lugar, se añadieron las reglas para `QTabWidget`, `QTabBar`, el divisor y las tarjetas secundarias transparentes directamente en [theme.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py). Además, se configuró para que los bordes del panel y botones del tab estén redondeados a excepción del borde superior izquierdo (`border-top-left-radius: 0px`), logrando un acople visual perfecto con el primer tab.

### 2. Formato de Mensajes con Marca de Tiempo (Timestamp)
- Modificación en [pipeline.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/pipeline.py) para incorporar la marca de tiempo `timestamp` en `ChatMessageDTO`.
- Se adaptó [main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/core/main_window_core.py) para que capture en tiempo real el tiempo del sistema en formato `HH:MM:SS` (usando `datetime.now()`) e inicialice los mensajes y canjes de puntos con la marca correspondiente.
- Se actualizó el renderizado en la vista del chat (`append_message`) para mostrar el prefijo `[HH:MM:SS]` estilizado en color gris apagado (`COLOR_NEUTRAL_500` / `#71717A`), manteniendo una estética premium y limpia.

### 3. Lógica del Sintetizador de Voz por Roles
- Se modificó [tts_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/tts/tts_service.py) para almacenar el `self._main_voice_id` global seleccionado por el usuario y permitir cambios rápidos y temporales de voz mediante encolamiento de tuplas `(text, voice_id)` en el hilo de reproducción.
- Se implementó la persistencia y carga de los ajustes individuales de voz por roles y proveedores (`tts_voice_{provider}_{role}`) en [chat_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/chat_service.py).
- Se añadió un resolvedor de prioridades por rol en [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) (`_resolve_voice_for_badges`), priorizando el rol en el orden `broadcaster` > `moderator` > `vip` > `subscriber` para elegir la voz que el lector del chat usará dinámicamente.

---

## Verificación y Resultados

- **Compilación de Sintaxis**: Se ejecutó `python -m py_compile` para todos los archivos Python modificados, resultando exitosa y confirmando que no existen errores sintácticos ni problemas de importación.
- **Validación Estructural**:
  - Las dependencias y pasaje de parámetros se han resuelto de forma segura usando valores opcionales, garantizando que el sistema no se caiga ni cause excepciones de tipo al no recibir marcas de tiempo o asignaciones vacías.
  - La sincronización asíncrona de los combo boxes de voces tras el cambio de motor de voz (Edge vs. SAPI5) opera correctamente usando el almacenamiento en caché de opciones pendientes.
