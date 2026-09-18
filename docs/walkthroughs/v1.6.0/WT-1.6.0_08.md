# Walkthrough - Compactación del Inspector de Chat Overlay y Nuevas Opciones de Personalización

## Novedades
- **Control de Límite Máximo de Mensajes en Pantalla (`max`)**: Se integró un control numérico de 5 a 50 mensajes en [`overlay_settings.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py), permitiendo a los streamers limitar la saturación en pantalla descartando automáticamente los mensajes más antiguos al alcanzar el tope.
- **Filtro de Ocultación de Comandos (`hide_commands`)**: Se añadió un interruptor para omitir automáticamente en el overlay todos los mensajes que inicien con el prefijo de comando `!` (como `!tts`, `!song`, `!discord`, etc.), manteniendo limpio el diseño en pantalla.
- **Visibilidad Opcional de Insignias de Roles (`show_badges`)**: Se añadió un interruptor para activar u ocultar las insignias de suscriptor, moderador, VIP y niveles en el overlay para quienes deseen una apariencia ultra-minimalista.
- **Visibilidad Opcional del Icono de Plataforma (`show_platform`)**: Se añadió un interruptor para activar u ocultar el logotipo de la plataforma (Kick, Twitch, YouTube, TikTok) antes del nombre de usuario.

## Mejoras
- **Rediseño Compacto de Alta Densidad (Estilo Inspector CAD / Figma / Blender)**:
  - Se eliminaron las 12 filas voluminosas individuales con descripciones largas que saturaban el espacio vertical (~900 px de altura total).
  - Se modularizó la interfaz en 3 tarjetas temáticas compactas con encabezados dedicados:
    1. **Estilo & Tipografía**: Selector de tema, entrada dual horizontal en paralelo para tamaño de fuente (`14 px`) y límite de mensajes (`15 msg`), y tiempo de permanencia en pantalla (`15 s`).
    2. **Disposición & Animación**: Selectores segmentados para orientación (vertical/horizontal), dirección del flujo y animación de entrada/origen.
    3. **Elementos & Filtros**: Matriz compacta en cuadrícula de 2 columnas (`QGridLayout`) con switches alineados, iconos temáticos y tooltips nativos completos.
    4. **Vista Previa & OBS URL**: Mockup dinámico y fila de copia de URL para OBS con estilo `action_outlined`.
- **Eficiencia Big-O en Renderizado y Filtrado**:
  - Filtrado de comandos $\mathcal{O}(1)$ en `chat.js` al evaluar el prefijo `!` antes de crear nodos en el DOM de OBS.
  - Menor recálculo de geometría y reducción en el árbol de widgets en PySide6.
- **Internacionalización (i18n)**:
  - Incorporadas todas las nuevas claves en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [`locale_defaults.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/locale_defaults.py) sin textos fijos o hardcodeados.

## Correcciones
- **Eliminación del Scroll Excesivo**: Se redujo drásticamente el espacio vertical ocupado por los controles en la pestaña de Overlay del chat, permitiendo una visión integral y ergonómica de todos los parámetros sin desplazamientos largos.
- **Sincronización de Parámetros URL OBS**: Se corrigió la discrepancia donde el overlay web en `chat.js` admitía `max` pero la UI de escritorio no ofrecía un control visual para gestionarlo ni persistirlo.
