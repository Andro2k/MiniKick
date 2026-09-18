# Walkthrough WT-1.6.0_11: Perfiles Individuales (Vertical / Horizontal) y Depuración del Chat Overlay

## Novedades

1. **Perfiles de Estilo Independientes por Orientación (`vertical` / `horizontal`)**:
   - Se implementó persistencia y gestión desacoplada de estilos estéticos (`theme`, `size`, `fade`, `flow`, `anim_in`) para el formato **Vertical** (columna) y el formato **Horizontal** (marquesina/ticker).
   - Al alternar la orientación en la interfaz, los controles cargan y recuerdan de forma inmediata los valores asignados a cada formato sin sobreescribir la configuración del otro.
   - El payload del websocket y la configuración activa transmiten las ramas `vertical`, `horizontal` y `common`, permitiendo que overlays en pantalla con distintas orientaciones operen simultáneamente con sus propios estilos.

2. **Detección Dinámica de Animación de Entrada (`anim-fade`, `anim-slide`, `anim-pop`)**:
   - En `assets/overlays/chat/chat.html`, se implementó la animación `@keyframes chatAnimFade` para desvanecimiento suave puro con opacidad progresiva.
   - La animación de deslizamiento (`.anim-slide`) ahora ajusta sus coordenadas de inicio automáticamente según la orientación y dirección del flujo (`flow-bottom-to-top`, `flow-top-to-bottom`, `flow-right-to-left`, `flow-left-to-right`), sin requerir selección manual del origen.

## Mejoras

1. **Compactación y Reestructuración Visual de Métricas (Grilla 2 Columnas)**:
   - Se retiró el control de límite de mensajes en pantalla (`spin_overlay_max`), eliminando configuraciones redundantes para el usuario final.
   - La tarjeta de **Estilo & Tipografía** (`card_style`) ahora presenta una grilla equilibrada de 2 columnas:
     - **Tamaño de Fuente**: [CompactSpinBox] `10 - 36 px` (icono `text-filled.svg`).
     - **Tiempo en Pantalla**: [CompactSpinBox] `0 - 120 s` (icono `stopwatch-filled.svg`).
   - El runtime web (`chat.js`) gestiona internamente la poda preventiva de nodos en el DOM (`MAX_SAFE_DOM_NODES = 50`) mediante `pruneMessages()`, protegiendo la memoria y fluidez de OBS Studio sin intervención manual.

2. **Eliminación del Selector "Origen de Animación"**:
   - Se removió el control `seg_overlay_entry` de la sección **Disposición & Animación**, simplificando la interfaz y dejando únicamente:
     - **Orientación del Chat** (`vertical` / `horizontal`).
     - **Dirección del Flujo** (adaptable contextualmente).
     - **Animación de Entrada** (`fade`, `slide`, `pop`).

3. **Eficiencia y Compatibilidad Retrospectiva**:
   - Complejidad $O(1)$ en la serialización y resolución de perfiles dentro de `ChatService.get_overlay_settings()` y `ChatController.get_active_overlay_config()`.
   - Se preservaron claves aplanadas de nivel raíz en `get_overlay_settings()` para retrocompatibilidad total con pruebas automatizadas y componentes existentes.

## Correcciones

1. **Desincronización en Dirección de Flujo (`flow`) y Animación (`anim_in`)**:
   - Corregido el problema donde la dirección del flujo y el tipo de animación no se incluían en el guardado de configuración ni en el broadcast por WebSocket hacia el cliente web del overlay.
   - Ahora ambos parámetros se persisten en base de datos bajo `chat_overlay_vertical_flow`, `chat_overlay_vertical_anim_in`, `chat_overlay_horizontal_flow` y `chat_overlay_horizontal_anim_in`, y se transmiten activamente en tiempo real.

2. **Fallback Silencioso de Animaciones en el Navegador**:
   - Solucionado el fallo en `chat.js` donde `anim_in === "fade"` caía en una clase de animación de desplazamiento por falta de definición CSS explícita.
