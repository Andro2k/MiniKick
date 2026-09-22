# Walkthrough - MiniKick v1.6.0 #30: Retiro Completo de la Opción "Desvanecimiento de Bordes" (Edge Fade)

## Novedades
- N/A (Versión de refactorización y limpieza de características en desuso).

## Mejoras
- **Limpieza de Interfaz de Usuario y Ajuste de Grid (`overlay_settings.py`)**:
  - Se eliminó el switch `sw_edge_fade` y su widget contenedor `item_edge` del panel de configuración del overlay.
  - Se reorganizó la cuadrícula de toggles (`grid_toggles`) a 7 elementos distribuidos armónicamente en 4 filas, ubicando el control de Bots en la fila 3 ocupando las 2 columnas (`grid_toggles.addWidget(item_bots, 3, 0, 1, 2)`).
- **Optimización de Renderizado en Mockup (`chat_mockup.py`)**:
  - Se retiró el atributo `self.edge_fade`, el parámetro `edge_fade` en `set_configuration`, la comprobación de cambios y el método `_draw_edge_fade(p, w, h)`.
  - Se eliminaron las operaciones de gradientes lineales de degradado (`QLinearGradient`) en cada repintado del canvas de previsualización, reduciendo el consumo de CPU y llamadas a `fillRect`.
- **Simplificación del Overlay Web (`chat.html`, `chat.js`)**:
  - Se removieron las reglas CSS `#chat-container.edge-fade` y `#chat-container.orientation-horizontal.edge-fade` con máscaras `-webkit-mask-image: linear-gradient(...)` de [chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html).
  - Se eliminó la variable `edgeFade`, la lectura de parámetros URL `urlParams.get('edge_fade')`, la inyección de clases CSS en el contenedor de mensajes y la reconciliación reactiva en `applyLiveConfig` dentro de [chat.js](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/js/chat.js).
- **Higiene de Diccionarios y Configuración (`chat_controller.py`, `chat_service.py`)**:
  - Eliminadas las claves `chat_overlay_edge_fade` y `edge_fade` del mapeo de configuración, sincronización por lotes (`save_settings`), y deserialización de persistencia local en almacenamiento de configuración.
- **Sincronización Estricta de Internacionalización (i18n)**:
  - Eliminadas las claves `edge_fade_title` y `edge_fade_desc` de [es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [locale_defaults.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/locale_defaults.py), manteniendo una paridad de claves del 100%.

## Correcciones
- **Pruebas Unitarias y Validaciones AST**:
  - Actualizados los casos de prueba en [test_chat_overlay_controls.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_chat_overlay_controls.py), [test_giphy_and_tts_filter.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_giphy_and_tts_filter.py) y [test_chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_chat_controller.py) para reflejar la eliminación de la propiedad y sus banderas.
  - Ejecución de la suite completa de pruebas: **50/50 pasadas con éxito**.
  - Validación con herramientas AST (`unused_parameter_manager.py`, `dead_code_manager.py`, `role_manager.py -v`) confirmando 0 parámetros huérfanos, 0 código muerto y 0 estilos/roles sin uso.
