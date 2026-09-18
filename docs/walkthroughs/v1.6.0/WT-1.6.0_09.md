# Walkthrough WT-1.6.0_09: Reorganización Compacta de Estilo y Reactividad Total del Mockup de Chat Overlay

## Novedades
- **Reactividad Completa en [ChatOverlayMockupWidget](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/chat_mockup.py)**: El componente de mockup ahora refleja dinámicamente en tiempo real cada uno de los filtros y elementos configurables del panel de ajustes:
  - **Insignias de Rol (`show_badges`)**: Al activarse/desactivarse, dibuja o suprime la insignia de rol (Moderador, Subscriptor, Creador) ajustando el espaciado sin dejar huecos vacíos.
  - **Icono de Plataforma (`show_platform`)**: Dibuja o suprime el icono de Kick / Twitch según el toggle.
  - **Desvanecimiento de Bordes (`edge_fade`)**: Aplica en tiempo de dibujo un degradado lineal sutil superior/inferior (en vertical) o lateral (en horizontal) que simula fielmente la máscara visual de OBS.
  - **Ocultar Comandos (`hide_commands`)**: Controla la visualización de mensajes de comando de prueba (ej. `!redes` / `!socials`), ocultándolos de la previsualización cuando el filtro está habilitado.
  - **Mostrar Bots (`show_bots`)**: Muestra o suprime el mensaje de bienvenida automático del bot en la previsualización.
  - **Emotes Grandes (`big_emotes`)**: Ajusta la escala tipográfica y presencia de emotes en el mensaje de demostración.
- **Mapeo de Ejemplos de Comandos en i18n**: Nuevas claves de localización (`preview_sample_cmd_msg` y `preview_sample_cmd_user`) agregadas en `locales/es.json` y `locales/en.json`.

## Mejoras
- **Distribución en 3 Columnas para [section_style](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py)**: Se rediseñó la tarjeta de estilo organizando los controles numéricos en un `QGridLayout` verticalmente apilado de 3 columnas:
  ```
  [icono] Tamaño de Fuente | [icono] Límite en Pantalla | [icono] Tiempo en Pantalla
  [CompactSpinBox]         | [CompactSpinBox]          | [CompactSpinBox]
  ```
  Cada celda posee encabezado con icono de 14px y etiqueta de rol `caption`, mientras que los [CompactSpinBox](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/widgets/controls_widget.py) se expanden uniformemente con `fixed_width=0` y factor de estiramiento 1:1:1.
- **Conexión de Señales en Tiempo Real**: Todos los switches de visibilidad (`sw_show_badges`, `sw_show_platform`, `sw_edge_fade`, `sw_hide_commands`, `sw_big_emotes`, `sw_overlay_show_gifs`) fueron conectados a `_update_mockup_preview` para actualización instantánea $\mathcal{O}(1)$ sin latencia.
- **Cálculo de Ancho Dinámico en Marquesina**: `_calculate_horizontal_width` ahora suma exclusivamente el ancho de los elementos activos (timestamp, badges, plataforma), asegurando que las píldoras horizontales mantengan una dimensión compacta exacta.

## Correcciones
- **Eliminación de Mayúsculas Forzadas en Encabezados de Card**: Se corrigió el método `_create_section_header` en [overlay_settings.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/chat/overlay_settings.py) removiendo `text.upper()`, permitiendo que los títulos de secciones ("Estilo & Tipografía", "Disposición & Animación", "Elementos & Filtros") se muestren con el formateo y tipografía natural del archivo de idioma.
- **Filtro de Bots en Mockup Vertical**: Corregido el bug donde el segundo mensaje de bot se dibujaba incondicionalmente en la previsualización vertical ignorando el estado de `show_bots`.
