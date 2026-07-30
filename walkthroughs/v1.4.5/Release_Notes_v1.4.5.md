# Release Notes | MiniKick v1.4.5
*Optimización de Empaquetado PyInstaller, Comando de Volumen para Moderadores, Estandarización de Tags de Música, Optimización Arquitectónica de Controllers, Evolución de !playlist y Scroll Invisible en Chat Overlay*

En esta versión (v1.4.5), MiniKick continúa su evolución incorporando nuevas herramientas de moderación, refinando la arquitectura de rendimiento del backend, reduciendo el tamaño del binario ejecutable `.exe` y mejorando la interacción en pantalla para transmisiones en vivo. Moveremos recursos estáticos fuera de `assets/` para evitar que PyInstaller empaquete imágenes innecesarias dentro del ejecutable, introducimos el nuevo comando `!vol` para modificar el volumen de la música desde el chat por parte de moderadores, estandarizamos la nomenclatura de tags de plugin a `[PLUGIN_MUSIC_*]`, refactorizamos los controladores principales para eliminar cuellos de botella $O(N)$ y riesgos de ReDoS, evolucionamos el comando `!playlist` para consultas rápidas por posición y habilitamos scroll invisible e inteligente en la fuente de chat para OBS.

---

## 1. Optimización del Binario Executable (PyInstaller & Inno Setup)
Reestructuramos la organización del repositorio para evitar que PyInstaller empaquete gráficos pesados no requeridos en tiempo de ejecución:
* **Separación de Capturas de Pantalla**: Trasladamos `assets/screenshots/` a `docs/screenshots/`, manteniendo actualizado el archivo [README.md](file:///c:/Users/TheAn/Desktop/python/Kick/README.md).
* **Recursos Gráficos del Instalador**: Trasladamos `assets/installer/` a `resources/installer/`, actualizando [instalador.iss](file:///c:/Users/TheAn/Desktop/python/Kick/instalador.iss).
* **Empaquetado Mínimo en `MiniKick.spec`**: Al quedar en `assets/` únicamente las fuentes (`fonts`), iconos (`icons`), overlays web (`overlays`) y cliente web (`web`), el `.exe` compilado por PyInstaller reduce significativamente su peso.

---

## 2. Comando de Volumen de Música (`!vol` / `!volume`)
Añadimos un comando de plugin dedicado para gestionar el volumen del reproductor directamente desde el chat de Kick:
* **Restricción Predeterminada para Moderadores**: Por defecto, el comando `!vol` sólo puede ser ejecutado por usuarios con rol de **Moderador** o superior.
* **Control en Interfaz UI**: Incorporamos un interruptor `Modificar Volumen (!vol)` en la pestaña de Comandos de Música ([commands_panel.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/commands_panel.py)).
* **Sincronización en Tiempo Real**: El controlador [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py) valida valores entre 0% y 100%, actualiza el volumen del proveedor activo (Spotify o YouTube) y mueve en tiempo real el control deslizante de volumen de la aplicación.

---

## 3. Estandarización de Tags de Plugin de Música (`[PLUGIN_MUSIC_*]`)
Homologamos los identificadores de plugin para reflejar la compatibilidad multiplataforma del reproductor (Spotify y YouTube):
* **Nomenclatura Unificada**: Los tags de sistema ahora se definen bajo la familia `[PLUGIN_MUSIC_*]`: `[PLUGIN_MUSIC_SR]`, `[PLUGIN_MUSIC_SKIP]`, `[PLUGIN_MUSIC_SONG]`, `[PLUGIN_MUSIC_PAUSE]`, `[PLUGIN_MUSIC_RESUME]`, `[PLUGIN_MUSIC_PLAYLIST]` y `[PLUGIN_MUSIC_VOLUME]`.
* **Retrocompatibilidad Total**: Se mantiene soporte completo en el despachador de eventos para comandos creados anteriormente bajo la etiqueta `[PLUGIN_SPOTIFY_*]`.

---

## 4. Optimización de Rendimiento y Arquitectura en Controllers
Realizamos una auditoría profunda basada en los 5 pilares arquitectónicos (SOLID, DRY, Seguridad OWASP y Complejidad Big-O) en [chat_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/chat_controller.py) y [music_controller.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py):
* **Prevención de ReDoS en Filtro de Palabras Prohibidas**: Compilamos un patrón unificado de expresión regular `\b(?:w1|w2|...)\b`, reduciendo la verificación de palabras bloqueadas de un bucle $O(N \times M)$ a una búsqueda en un solo pase $O(M)$.
* **Búsquedas $O(1)$ en Asignación de Voces TTS**: Almacenamos el mapa de IDs de voz en la caché `_available_voice_ids`, eliminando la creación repetitiva de conjuntos en memoria por cada mensaje de chat.
* **Seguridad de Hilos Worker**: Reemplazamos terminaciones abruptas de hilos por interrupciones controladas (`requestInterruption()`), evitando bloqueos o corrupción de sockets.

---

## 5. Evolución del Comando `!playlist` (`!queue`, `!pl`)
Rediseñamos la respuesta del comando de lista de reproducción para evitar mensajes extensos en chats concurridos:
* **Consulta Rápida (`!playlist`)**: Muestra únicamente los números de posición en la cola asignados al usuario que ejecuta el comando (ej: `🎵 @usuario, tienes 2 canción(es) en la cola: #2, #5`).
* **Consulta de Canción Específica (`!playlist 2` o `!pl 2`)**: Muestra el título, artista y usuario que pidió la canción ubicada en esa posición de la cola (ej: `🎵 Canción #2: "Título" - Artista (pedida por @usuario)`).

---

## 6. Scroll Invisible e Inteligente en Overlay de Chat para OBS
Mejoramos la fuente de navegador del chat overlay ([chat.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/chat/chat.html)) para software de transmisión:
* **Soporte para Rueda del Ratón**: El contenedor de mensajes ahora permite desplazarse verticalmente.
* **Barra de Scroll Invisible**: Ocultamos la barra visual de desplazamiento (`scrollbar-width: none;`), manteniendo una estética limpia e integrada en OBS.
* **Auto-Scroll Inteligente**: Los mensajes nuevos desplazan el chat hacia abajo automáticamente, pero si el usuario sube manualmente para leer un mensaje antiguo, el desplazamiento se pausa temporalmente.
