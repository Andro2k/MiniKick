# Walkthrough WT-1.5.8_36: Soporte para Alertas Personalizadas en HTML/HTM con Servidor de Medios y PostMessage

## 1. Contexto y Objetivos

Los creadores de contenido y streamers suelen requerir un nivel de personalización visual superior para sus alertas en vivo (animaciones avanzadas en Canvas 2D/WebGL, librerías CSS externas, tipografías interactivas, animaciones SVG y efectos de partículas). Anteriormente, el sistema de alertas de MiniKick únicamente permitía la selección de archivos de imagen (`.gif`, `.png`, `.jpg`, etc.) o video (`.mp4`, `.webm`).

El objetivo principal de esta implementación fue:
1. **Permitir archivos `.html` y `.htm` locales** en la configuración de medios de las alertas de MiniKick.
2. **Servir archivos HTML locales y sus recursos relativos** (CSS, JavaScript, imágenes, tipografías) de forma segura a través del servidor HTTP local de overlays (`OverlayServer`).
3. **Garantizar seguridad estricta contra Path Traversal** y validar tokens de sesión en cada solicitud HTTP de medios del usuario.
4. **Facilitar la resolución relativa de recursos en el navegador** codificando la ruta del directorio base en la estructura de la URL.
5. **Establecer un protocolo de comunicación bidireccional vía `window.postMessage`** entre el overlay principal (`alerts.html`) y el iframe de la alerta personalizada, permitiendo recibir datos del evento (`onEventReceived`) y finalizar anticipadamente la alerta (`minikick:finish_alert`).
6. **Cumplir estrictamente con i18n** sin cadenas de texto codificadas en duro y proporcionar una plantilla interactiva de ejemplo lista para usar.

---

## 2. Cambios Implementados

### A. Capa de Internacionalización (i18n) ([locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json), [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json))
- Actualizadas las claves de internacionalización para incorporar extensiones `.html` y `.htm` en los filtros y descripciones:
  - `alerts.fields.media_filter`: `"Archivos de medios (*.gif *.png *.jpg *.jpeg *.webp *.mp4 *.webm *.html *.htm)"` / `"Media files (*.gif *.png *.jpg *.jpeg *.webp *.mp4 *.webm *.html *.htm)"`.
  - `alerts.fields.media`: `"Archivo de Imagen / Video / HTML"` / `"Image / Video / HTML File"`.
  - `alerts.fields.media_placeholder`: `"Ruta del archivo (GIF, MP4, HTML, WebM, PNG, etc.)"` / `"File path (GIF, MP4, HTML, WebM, PNG, etc.)"`.

### B. Interfaz Gráfica de Usuario ([frontend/components/alerts/event_card.py](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/alerts/event_card.py))
- En `_browse_media()`, se reemplazó el filtro hardcodeado previo por `self.i18n.get("alerts.fields.media_filter")`.
- Al abrir el diálogo `QFileDialog.getOpenFileName()`, el usuario puede seleccionar archivos `.html` y `.htm` junto con los formatos multimedia estándar.

### C. Backend: Orquestación de Alertas ([backend/services/overlay/overlay_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_manager.py))
- En `trigger_alert()`:
  - Se detecta si la extensión del archivo corresponde a `.html` o `.htm`.
  - Si es HTML local, se obtiene el directorio contenedor del archivo (`os.path.dirname(media_path)`).
  - La ruta del directorio se codifica en Base64 URL-safe y se estructura la URL pública de medios:
    `http://localhost:{port}/user_media/{session_token}/{b64_dir}/{filename}`
  - Esto garantiza que cuando el navegador cargue el HTML e interprete recursos relativos como `<link rel="stylesheet" href="style.css">` o `<script src="script.js">`, el navegador conserve automáticamente el prefijo `/user_media/{token}/{b64_dir}/` sin requerir parámetros de consulta `?token=...` que los navegadores descartan en rutas relativas.

### D. Backend: Servidor HTTP y Mitigación de Path Traversal ([backend/services/overlay/overlay_routes.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/overlay/overlay_routes.py))
- **Factorización Limpia de Streaming de Archivos**: Se unificó la lógica de lectura y respuesta HTTP en `_serve_file(self, filepath)`, reduciendo duplicación de código.
- **Ruta `/user_media/` con Validación Estricta**:
  - Implementado `_handle_user_media_request(self, path)`.
  - Extrae y valida el token de sesión de la ruta contra `self.server.session_token`.
  - Decodifica el directorio base codificado en Base64.
  - Normaliza la ruta solicitada con `os.path.abspath` y `os.path.realpath`.
  - **Mitigación Path Traversal**: Verifica de forma determinista que:
    `os.path.commonpath([abs_root, abs_target]) == abs_root`
    Bloqueando intentos de acceso con secuencias `..` o rutas fuera del directorio autorizado (HTTP 403 Forbidden).
  - Determina el `Content-Type` adecuado mediante `mimetypes.guess_type` y entrega el archivo.
- **Bypass de Token en Query Params para `/user_media/`**:
  - En `do_GET()`, se añadió la exención `is_user_media = path.startswith("/user_media/")` para que las peticiones a medios de usuario validen su token directamente desde la ruta de URL en lugar de los query params.

### E. Frontend Web: Overlay de Alertas ([assets/overlays/alerts/alerts.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/alerts.html))
- **Soporte para `<iframe>` en el Contenedor de Medios**:
  - En `showAlert()`, si `media_ext === 'html' || media_ext === 'htm'`, se genera un elemento `<iframe>` embebido con fondo transparente (`allowtransparency="true"`, `frameborder="0"`).
  - Al cargar el iframe (`iframe.onload`), se despacha un evento `postMessage` hacia la ventana del iframe:
    ```javascript
    iframe.contentWindow.postMessage({
        type: "onEventReceived",
        detail: {
            listener: data.alert_type,
            event: data
        }
    }, "*");
    ```
  - Se añadió la clase CSS `#alert-container.custom-html-active` para adaptar el layout en modo de alerta HTML de pantalla completa o personalizada.
- **Escucha de Mensajes para Descarte Anticipado**:
  - Se implementó `onCustomAlertMessage(event)` escuchando `minikick:finish_alert` o `finish_alert`.
  - Permite que el código JavaScript de la alerta personalizada notifique al overlay cuando sus animaciones concluyen, cerrando la alerta de inmediato sin esperar al temporizador máximo.

### F. Plantilla Interactiva de Ejemplo ([assets/overlays/alerts/custom_alert_example.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/alerts/custom_alert_example.html))
- Se creó una plantilla completa y autocontenida que demuestra:
  1. Estilos modernos con degradados y tipografías limpias.
  2. Canvas 2D interactivo con animación de fuegos artificiales y partículas.
  3. Recepción del evento mediante `window.addEventListener('message', ...)`.
  4. Extracción dinámica del usuario, tipo de alerta y mensaje personalizado.
  5. Envío de `window.parent.postMessage({ action: "minikick:finish_alert" }, "*")` al concluir la animación.

---

## 3. Análisis de Complejidad Big-O

- **Validación de Rutas y Tokens**: $\mathcal{O}(1)$ tiempo y $\mathcal{O}(1)$ espacio auxiliar. La validación del token de sesión es una comparación directa de cadenas, la decodificación Base64 de la ruta del directorio es proporcional a la longitud fija del path, y la verificación de contención de ruta con `os.path.commonpath` se ejecuta en tiempo lineal sobre la profundidad del path ($\mathcal{O}(d)$ donde $d \le 10$, virtualmente $\mathcal{O}(1)$).
- **Streaming de Archivos**: $\mathcal{O}(S)$ donde $S$ es el tamaño del archivo multimedia/código, transmitido en bloques de 64 KB sin saturar memoria RAM.
- **Despacho de Eventos en Navegador**: $\mathcal{O}(1)$ para el envío y recepción de mensajes `postMessage`.

---

## 4. Verificación y Pruebas Automatizadas

Se creó una suite exhaustiva de pruebas unitarias en [resources/tests/unit/services/test_user_media_routes.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/services/test_user_media_routes.py):

1. **`test_user_media_serving`**: Verifica que un archivo `.html` en un directorio temporal sea servido correctamente con código HTTP 200 y `Content-Type: text/html`.
2. **`test_user_media_relative_css_serving`**: Simula una solicitud relativa de CSS (`style.css`) resolviéndose dentro del mismo directorio base codificado, retornando 200 y `Content-Type: text/css`.
3. **`test_user_media_invalid_token`**: Verifica que peticiones con tokens incorrectos o ausentes sean rechazadas con HTTP 403 Forbidden.
4. **`test_user_media_path_traversal_blocked`**: Intenta acceder a archivos del sistema fuera del directorio raíz permitido mediante secuencias `..%2F..%2F`, verificando que el servidor bloquee el intento con HTTP 403 Forbidden.

### Resultados de Ejecución:
- **Pruebas de Rutas de Medios**:
  ```bash
  uv run pytest resources/tests/unit/services/test_user_media_routes.py
  # Resultado: 4 passed in 0.65s (100%)
  ```
- **Integridad de i18n**:
  ```bash
  uv run pytest resources/tests/unit/ui/test_i18n_integrity.py
  # Resultado: 3 passed in 0.98s (100%)
  ```
- **Suite Completa de Servicios**:
  ```bash
  uv run pytest resources/tests/unit/services/
  # Resultado: 58 passed in 2.89s (100%)
  ```
