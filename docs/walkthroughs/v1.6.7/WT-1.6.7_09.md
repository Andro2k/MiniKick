# Walkthrough Técnico — MiniKick v1.6.7 (Paso 09)

Se limpió el theme para que cada color y cada medida exista en un solo lugar: se eliminaron las constantes que solo repetían valores de otra clase y las constantes sin uso. También se revisó el diagnóstico de latencia de Kick (paso 06) y se corrigió un efecto secundario del watchdog. Módulos afectados: `frontend/common/theme.py`, los mockups de música, alertas y chat, la lista de insignias del chat y el proveedor del WebSocket de Kick.

---

## Novedades

- Prueba `test_theme_color_constants_are_never_duplicated_across_classes`: falla si dos constantes de color distintas repiten el mismo valor hexadecimal.
- Prueba `test_size_owns_radius_and_margin_without_module_level_copies`, que fija `Size.Radius` y `Size.Margin` como única forma de acceso.

## Mejoras

- `MockupPalette` conserva solo sus colores propios (música y degradados de avatar). Se eliminaron 14 constantes que apuntaban a `Palette` (`MUSIC_VINYL_BLACK`, `MUSIC_VINYL_HOLE`, `MUSIC_METAL_DARK`, `MUSIC_TONEARM`, `MUSIC_HEAD_BORDER`, `MUSIC_HEAD_BG`, `MUSIC_GROOVE`, `ALERT_PREVIEW_*` y `CHAT_PREVIEW_SURFACE`); los mockups usan `Palette.NEUTRAL_*` directamente. `BadgeTheme.BADGE_BCG` se eliminó por la misma razón.
- `Radius` y `Margin` dejaron de existir como clases de módulo reexportadas dentro de `Size`; ahora son clases anidadas de `Size`. El acceso `Size.Radius.RAD_*` y `Size.Margin.MRG_*` no cambia.
- Las asas del scrollbar usan `rgba(Palette.NEUTRAL_000, alfa)` en lugar de repetir valores `rgba(255, 255, 255, ...)`.
- Se eliminaron `Borders.BRD_HOVR`, `Borders.BRD_KICK` y `Borders.BRD_FAIL`, que no se usaban en código de producción.
- Las sondas de solo RTT del watchdog de Kick ya no activan el cierre por timeout del socket; ese cierre sigue aplicándose únicamente al ping por inactividad. Se ajustaron las notas del paso 06 y del registro INC-049.

## Correcciones

- Una respuesta de pong lenta a una sonda de diagnóstico podía forzar el cierre y la reconexión del socket con el chat activo.
- Indentación de dos retornos de guarda en `_warn_slow_message`.

> [!NOTE]
> Los valores resultantes de cada constante y el QSS global generado (tamaños base 10, 12 y 14) son idénticos a los de antes del cambio; solo se eliminaron nombres.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Comparación de todas las constantes del theme y del QSS global antes y después | 18 nombres eliminados, 0 valores modificados, QSS idéntico en tamaños 10, 12 y 14 |
| `test_theme_tokens.py` y `test_kick_ws_heartbeat.py` | 2 y 19 aprobadas |
| Los 14 archivos de `resources/tests`, uno por proceso | 13 completos en verde; en `test_worker_and_core_lifecycle.py` falla 1 de 12 (`test_chat_and_reward_workers_stop_sets_interruption_and_quit`, intermitente y también falla sin estos cambios) |
| Suite rápida de auditorías de calidad | 11 de 12 aprobadas; falla Project Translation Keys por `music.youtube.com` en `backend/utils/youtube_url.py`, ajena a este paso |
| Entorno | Python 3.12 en la verificación; el proyecto declara 3.14 |
