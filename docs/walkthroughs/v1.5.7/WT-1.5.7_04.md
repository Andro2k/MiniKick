# Walkthrough: Soporte de Colores de Plataforma e Iconos Tintados en `ModernModal`

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_04.md`  
**Módulos Modificados:**
- [`frontend/common/paths.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/paths.py)
- [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)
- [`frontend/dialogs/base_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py)
- [`frontend/dialogs/tiktok_connect_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/tiktok_connect_dialog.py)
- [`frontend/dialogs/youtube_connect_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/youtube_connect_dialog.py)
- [`resources/tests/unit/ui/test_dialogs.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_dialogs.py)

---

## 1. Resumen de Cambios

1. **Resolución de Rutas de Iconos (`paths.py`)**:
   - `resolve_icon_path` ahora soporta nombres base (`"brand-tiktok.svg"`), rutas relativas con carpeta (`"icons/brand-tiktok.svg"`) y rutas absolutas devueltas por `get_assets_path`.

2. **Roles de Superficie para Plataformas en `theme.py`**:
   - Se agregaron roles específicos para contenedores circulares de iconos:
     - `QFrame[role="tiktok_icon"]`: `COLOR_TIKTOK` (`#00F2FE`).
     - `QFrame[role="youtube_icon"]`: `COLOR_YOUTUBE` (`#FF0000`).
     - `QFrame[role="twitch_icon"]`: `COLOR_TWITCH` (`#9146FF`).
     - `QFrame[role="black_icon"]`: `COLOR_BLACK` (`#000000`).

3. **Despacho Dinámico y Tintado en `ModernModal` (`base_dialog.py`)**:
   - Se implementó `role_dispatch` para mapear automáticamente colores (`COLOR_TIKTOK`, `COLOR_YOUTUBE`, `COLOR_TWITCH`, `COLOR_RED`, `COLOR_GREEN`, `COLOR_AMBER`, `COLOR_BLUE`, `COLOR_BLACK`) a su rol de QSS y color de primer plano contrastante (ej. icono negro sobre cian de TikTok, blanco sobre rojo de YouTube).
   - Se integró `get_pixmap_colored` para rasterizar los SVGs en su escala y color exacto.

4. **Actualización de Diálogos**:
   - `TikTokConnectDialog` configurado con `icon_bg_color=COLOR_TIKTOK`.
   - `YouTubeConnectDialog` configurado con `icon_bg_color=COLOR_YOUTUBE`.

---

## 2. Verificación y Resultados

```powershell
uv run pytest resources/tests/unit/ui/test_dialogs.py
```
- **4/4 tests aprobados (100% PASSED)**.
