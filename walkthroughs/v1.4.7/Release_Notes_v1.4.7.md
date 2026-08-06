# Release Notes - MiniKick Version v1.4.7

> [!NOTE]
> MiniKick v1.4.7 introduce una gran actualización enfocada en **eliminación total del destello de arranque**, **sincronización y unificación real del reproductor de música**, **aceleración GPU por Canvas 2D en widgets overlay**, **monitoreo multitrama de red**, **protección anti-spam inteligente sin falsos positivos por emotes** y **optimización completa de voces TTS por roles**.

---

## Novedades Destacadas

> [!IMPORTANT]
> **Eliminación Definitiva de la Ventana Fantasma de Arranque (`160x100`)**
> - **Diagnóstico de Ventanas Huérfanas:** Inspección profunda del ciclo de vida de PySide6 reduciendo las ventanas flotantes en `QApplication.topLevelWidgets()` de 41 a **0**.
> - **Bloqueo de Renderizado Nítido:** Implementación de `setUpdatesEnabled(False)` y dimensionamiento preventivo `resize(1100, 750)` al iniciar `MainWindowCore`, evitando que Windows pinte el marco nativo provisional de 160x100.
> - **Propagación Completa de `parent`:** Enlace jerárquico estricto en las 11 Vistas Principales, Tarjetas (`ModernCard`), Contenedores (`QStackedWidget`), Diálogos (`ModernFramelessShell`) y Desplegables (`NoWheelComboBox`).

---

## Reproductor de Música y Volumen Unificado

> [!TIP]
> **Sincronización en Tiempo Real y Control de Límites**
> - **Instancia Única de Proveedor de Música:** Eliminada la duplicación de `YouTubeMusicProvider`, transfiriendo el proveedor desde `AppContainerCore` hasta `MusicController`. El volumen ajustado en el slider afecta inmediatamente a la reproducción activa.
> - **Hidratación Visual de Ajustes:** Implementación de `set_rate_limit_values` para refrescar automáticamente los 4 sliders de límites (canciones por usuario, cooldown, tamaño de cola y duración máxima) al abrir el panel de música.

---

## Motor Canvas 2D Acelerado por GPU para Widgets Overlay

- **Ráfagas de Emotes a 60 FPS sin Lag:** Reescritura completa del widget de explosión de emotes migrando de nodos del DOM a un lienzo HTML5 Canvas 2D. Permite renderizar ráfagas masivas de 50, 100 o más partículas a 60 FPS estables sin provocar tirones ni reflows en OBS.
- **Rango de Partículas Configurable:** Se amplió la capacidad en la configuración del widget para permitir ráfagas de 5 a 100 emoticones.
- **Barra de Combo Fluida:** Animación del temporizador del combo de emotes migrada a `requestAnimationFrame` eliminando saltos de fotogramas.

---

## Rediseño Integral de Overlays y Configuración TTS

- **Gama Global de Voces TTS:** Eliminación del filtro por región en la interfaz para desplegar el catálogo completo de voces (locales y Edge Web) en todos los roles (Streamer, Moderador, VIP, Suscriptor y General).
- **Chat Overlay Responsivo:** Soporte para modo Vertical y modo Marquesina Ticker Horizontal con insignias inline (`STREAMER`, `BOT`, `MODERATOR`) y colores pastel personalizados por usuario.
- **5 Diseños de Reproductor de Música:**
  1. *Vinyl:* Tocadiscos retro con disco de vinilo en rotación 360 grados continua.
  2. *Banner:* Tarjeta vertical tipo poster con portada extendida.
  3. *Pill:* Cápsula minimalista horizontal con ecualizador animado.
  4. *Compact:* Tarjeta apilada compacta.
  5. *Standard:* Barra de reproducción clásica extendida.

---

## Monitoreo de Red Multitrama en Tiempo Real

- **Soporte para 6 Servicios Clave:** Seguimiento dinámico continuado (50 muestras) para Internet, Kick API, Chat WebSocket, Overlay Local, Spotify API y YouTube.
- **Barra de Filtros (Pills):** Permite aislar servicios individuales o visualizar la gráfica global con un solo clic.
- **Métricas de Estabilidad:** Cálculo en $\mathcal{O}(N)$ de Ping Actual, Promedio, Mínimo, Máximo, Jitter (variación en ms) e Indicador de Estabilidad (Óptima, Buena, Regular, Deficiente).

---

## Filtro Anti-Spam Inteligente sin Falsos Positivos

- **Descuento de Emotes de Kick:** La protección de símbolos y caracteres extraños elimina las etiquetas de emotes (`[emote:ID:NOMBRE]`) antes del cálculo, evitando sanciones injustas a usuarios legítimos.
- **Límite de Caracteres por Mensaje:** Filtro de bloques de texto refinado con rangos de 50 a 2000 caracteres e inspección de saltos de línea.
- **Interfaz Dinámica:** Desactivación automática del selector de tiempo cuando la sanción elegida no requiere timeout.

---

## Seguridad en Respaldos y Bypass Anti-Bot de YouTube

> [!WARNING]
> **Bypass de Detección de Bot en YouTube**
> Estrategia cascada prioritaria en `yt-dlp` eliminando bloqueos anti-bot y log-spamming.

- **Salto Automático de Canciones:** Avance inmediato en menos de 1.5s ante videos con restricción de edad, notificando amigablemente en el chat de Kick.
- **Seguridad en Respaldos:** Aislamiento de fichas de sesión de overlay en exportaciones JSON y derivación dinámica de metadata usando la versión de la aplicación.

---

## Comparativa de Eficiencia y Rendimiento (Big-O)

| Módulo / Operación | Comportamiento Anterior | Optimización v1.4.7 | Impacto en Rendimiento |
|---|---|---|---|
| Inicialización de UI (Ventanas Qt) | 41 ventanas flotantes huérfanas en Qt | Jerarquía `parent=self` + `setUpdatesEnabled(False)` | 0 parpadeos/destellos al iniciar la aplicación |
| Control de Volumen de Música | Instancia duplicada / Volumen fijo | Instancia unificada de `YouTubeMusicProvider` | Sincronización instantánea de volumen en tiempo real |
| Renderizado de Explosión de Emotes | Nodos DOM por fotograma | Lienzo HTML5 Canvas 2D GPU | 60 FPS estables con 100+ partículas sin DOM reflows |
| Monitoreo de Red | 2 servicios fijos | 6 servicios con matriz $\mathcal{O}(N)$ | Monitoreo en tiempo real de toda la infraestructura |
| Sanitización de Errores YouTube | Retraso de 15s en lectura de cookies | Fallo rápido $\mathcal{O}(1)$ en menos de 1.5s | Salto automático inmediato sin congelar la lista |
| Procesamiento de Filtros Anti-Spam | Falsos positivos con emotes | Regex $\mathcal{O}(N)$ con strip previo de emotes | 0 sanciones erróneas por emoticones de Kick |
| Selector de Voces TTS | Filtrado restrictivo por región | Catálogo unificado global de voces | Acceso inmediato a todas las voces en cualquier rol |

---

> [!CAUTION]
> **Notas de Actualización:**
> La versión 1.4.7 incluye todas las soluciones acumuladas en los walkthroughs `WT-1.4.7_01` al `WT-1.4.7_09`. Al iniciar la aplicación notarás una apertura limpia, instantánea y sin destellos de ventanas flotantes.
