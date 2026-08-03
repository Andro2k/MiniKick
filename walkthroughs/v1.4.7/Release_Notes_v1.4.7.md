# Release Notes v1.4.7 - MiniKick

## 🚀 Nuevas Características y Mejoras de Overlays

### 💬 Overlay de Chat Horizontal y Personalizable
- **Soporte de Chat Horizontal (Ticker)**: Nuevo formato de marquesina horizontal ideal para barras superiores o inferiores en transmisiones.
- **Control de Flujo de Mensajes**: Selección independiente de la dirección hacia la que avanzan los chats:
  - Vertical: De abajo hacia arriba (`bottom-to-top`) o De arriba hacia abajo (`top-to-bottom`).
  - Horizontal: De derecha a izquierda (`right-to-left`) o De izquierda a derecha (`left-to-right`).
- **Origen de Animaciones Personalizable**: Elige si los nuevos mensajes ingresan desde Abajo, Arriba, Izquierda o Derecha.

### 🎵 Múltiples Diseños y Tema Dinámico para Overlay de Música
- **5 Estilos de Layout Visuales**:
  - `banner`: Header superior de carátula grande con gradiente elegante.
  - `pill`: Cápsula minimalista ultracompacta.
  - `floating`: Deck de cristal con portada flotante.
  - `compact`: Tarjeta compacta con ecualizador animado.
  - `standard`: Barra horizontal clásica.
- **Dynamic Theme (Auto-Color de Álbum)**: Extracción en tiempo real del color dominante del cover art usando Canvas HTML5 $\mathcal{O}(1)$ para adaptar gradientes, acentos y resplandor al diseño de la portada activa.

---
*MiniKick v1.4.7*
