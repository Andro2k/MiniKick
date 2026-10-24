# Walkthrough Técnico — MiniKick v1.6.5 (Paso 04)

Auditoría completa de los 34 archivos `__init__.py` del proyecto. Se identificaron y corrigieron desincronizaciones entre los bloques `from ... import` y los listados `__all__`, que generaban falsos positivos masivos en el IDE (Pylance/Pyright). Los símbolos afectados estaban activos en producción pero el linter los catalogaba como "no exportados" o "no usados".

---

## Novedades

No se incorporaron nuevas características en esta iteración.

---

## Mejoras

### `frontend/common/__init__.py` — Sincronización completa del `__all__` (37 símbolos)

El `__all__` estaba severamente desincronizado respecto a los bloques de importación. Se agregaron 37 símbolos que estaban correctamente importados y usados en producción, pero ausentes del listado público. El efecto inmediato es la eliminación de todos los falsos positivos de IDE sobre tokens de diseño y utilidades.

Símbolos incorporados al `__all__` agrupados por categoría:

- **Validators:** `sanitize_command_trigger`, `is_complete_valid_trigger`
- **Colores base:** `COLOR_PURE_WHITE`
- **Colores green:** `COLOR_GREEN_HOVER`, `COLOR_GREEN_SOLID`
- **Colores red:** `COLOR_RED_HOVER`, `COLOR_RED_SOLID`, `COLOR_DANGER_SURFACE`
- **Colores orange:** `COLOR_ORANGE`, `COLOR_ORANGE_DARK`, `COLOR_ORANGE_HOVER`, `COLOR_ORANGE_GLOW`
- **Plataformas:** `COLOR_KICK`, `COLOR_KICK_REWARDS`, `COLOR_KICK_BORDER`, `COLOR_TWITCH_LIGHT`
- **Borders:** `COLOR_BORDER_MUTED_FOCUS`, `COLOR_BORDER_TOP_SHINE`
- **Badges:** `COLOR_BADGE_STREAMER`, `COLOR_BADGE_MODERATOR`, `COLOR_BADGE_VIP`, `COLOR_BADGE_OG`, `COLOR_BADGE_SUB`, `COLOR_BADGE_BG`
- **Switch tokens (14):** `COLOR_SWITCH_TRACK_OFF_0/1`, `COLOR_SWITCH_BORDER_OFF`, `COLOR_SWITCH_TRACK_ON_0/1`, `COLOR_SWITCH_TRACK_DIS_0/1`, `COLOR_SWITCH_THUMB_OFF_0/1`, `COLOR_SWITCH_THUMB_ON_0/1`, `COLOR_SWITCH_THUMB_DIS_0/1`
- **Misc:** `COLOR_MEDIA_THUMB_BG`, `COLOR_SYNTAX_VARIABLE`

Adicionalmente, el `__all__` fue reorganizado con comentarios de agrupación semántica para facilitar su mantenimiento futuro.

### `frontend/components/__init__.py` — Re-exportación de `ChatSpamPanel`

`ChatSpamPanel` estaba correctamente declarado y exportado en el sub-paquete `frontend/components/chat/__init__.py`, pero no re-exportado desde el paquete padre `frontend/components`. Se agregó al bloque `from .chat import (...)` y al `__all__` para mantener consistencia con todos los demás paneles del módulo `chat`.

### `backend/services/__init__.py` — Re-exportación de 3 símbolos del sub-paquete `chat`

Tres símbolos disponibles en `backend/services/chat/__init__.py` no estaban accesibles desde la raíz del paquete `backend/services`. Se incorporan al bloque `from .chat import (...)` y al `__all__`:

- `PiperVoiceDownloadWorker` — worker de descarga de voces Piper
- `DEFAULT_PIPER_VOICE_ID` — constante de voz Piper por defecto
- `GiphyService` — servicio de integración con Giphy

### `frontend/widgets/__init__.py` — Limpieza de `BaseView` del `__all__`

`BaseView` aparecía declarado en el `__all__` de `frontend/widgets` sin estar importado directamente en el módulo — solo existía como carga perezosa en un `__getattr__`. Dado que `BaseView` pertenece a `frontend/views` y no a `frontend/widgets`, se eliminó únicamente del `__all__`. El bloque `__getattr__` se preserva intencionalmente: es necesario en runtime para que los consumidores existentes (como `commands_view.py`) puedan hacer `from frontend.widgets import BaseView` sin provocar importaciones circulares. La mejora es que el linter deja de reportar "declared in `__all__` but not imported", mientras el acceso en runtime sigue funcionando correctamente.

---

## Correcciones

- **Falsos positivos masivos de IDE eliminados:** 37 tokens de diseño (`COLOR_*`, `MARGIN_*`, `SPACING_*`, etc.) y 2 utilidades de validación del módulo `frontend/common` eran marcados como "no exportados" o "sin uso" por Pylance/Pyright. La causa raíz era la ausencia de estos símbolos en el `__all__`, no una falta de uso real. Todos estaban en uso activo en componentes de producción. Corregido sincronizando el `__all__` con los bloques `from ... import` de cada módulo.

- **Inconsistencia de profundidad de importación en `ChatSpamPanel`:** El consumidor `chat_view.py` importaba `ChatSpamPanel` directamente del sub-paquete `frontend.components.chat` en lugar de hacerlo desde `frontend.components`, rompiendo la convención del proyecto. La corrección en el paquete padre permite que el consumidor use indistintamente cualquiera de las dos rutas de forma coherente.

