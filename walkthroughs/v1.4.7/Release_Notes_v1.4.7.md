# Release Notes v1.4.7 - MiniKick

## 🚀 Nuevas Características y Mejoras de Overlays

### 💬 Overlay de Chat Horizontal y Personalizable
- **Soporte de Chat Horizontal (Ticker)**: Nuevo formato de marquesina horizontal ideal para barras superiores o inferiores en transmisiones.
- **Control de Flujo de Mensajes**: Selección independiente de la dirección hacia la que avanzan los chats:
  - Vertical: De abajo hacia arriba (`bottom-to-top`) o De arriba hacia abajo (`top-to-bottom`).
  - Horizontal: De derecha a izquierda (`right-to-left`) o De izquierda a derecha (`left-to-right`).
- **Origen de Animaciones Personalizable**: Elige si los nuevos mensajes ingresan desde Abajo, Arriba, Izquierda o Derecha.

### 🎵 Múltiples Diseños y Tema Dinámico para Overlay de Música
- **5 Estilos de Layout Visuales**: `banner`, `pill`, `floating`, `compact`, `standard`.
- **Dynamic Theme (Auto-Color de Álbum)**: Extracción en tiempo real del color dominante del cover art usando Canvas HTML5 $\mathcal{O}(1)$.

### ⚡ Optimización y Resiliencia en Reproducción de YouTube Music
- **Cascada Multicliente Antibot**: Implementación de 5 estrategias de `player_client` (`tv_embedded`, `web_embedded`, `ios`, `android`, `mweb`, `web_creator`, `android_vr`, `tv`) para evitar errores de restricción de edad y detección de bots.
- **Soporte Transparente de Cookies**: Detección automática de cookies de navegador (`Chrome`, `Edge`, `Firefox`, `Brave`, `Opera`, `Vivaldi`) y archivos `cookies.txt` en la carpeta `.Minikick`.
- **Extracción Óptima de Stream Directo**: Filtrado en tiempo lineal $\mathcal{O}(n)$ del mejor formato de audio para streaming instantáneo en `QMediaPlayer`.

---
*MiniKick v1.4.7*


