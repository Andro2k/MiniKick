# WT-1.5.9_01: Calibración y Auditoría de Estilos en `role_manager.py`

- **Versión**: v1.5.9
- **Tipo**: Fix / Tooling Enhancement
- **Componente**: [`resources/tools/role_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/role_manager.py)

---

## 1. Descripción del Problema
Al remover selectores o llamadas `setProperty("role", ...)` en el código del frontend (como `divider.setProperty("role", "searchable_combo_divider")`), la herramienta [`role_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/role_manager.py) continuaba reportando `✅ [PASS] All roles and states used in the codebase are validly defined in theme.py!`. 

Esto ocurría porque:
1. La verificación de roles sin uso (`unused_roles`) estaba delegada únicamente a la bandera opcional `-v` como mero `[INFO]`, ignorando estados sin uso y aprobando la ejecución por defecto.
2. La inspección AST original descartaba llamadas con ternarios (`ast.IfExp`), argumentos personalizados (`btn_role`, `icon_role`, `button_role`), llamadas a métodos de estado (`set_dialog_state`) y tablas de despacho de iconos.
3. No existía trazabilidad de línea para ubicar dónde se definía cada rol o estado dentro de [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py).

---

## 2. Solución Aplicada

1. **Estructura de Datos `ThemeDefinition`**:
   - Se modificó `parse_theme_qss` para mapear cada rol y estado a un `ThemeDefinition` que incluye tipos de widgets asociados, números de línea precisos en `theme.py` y sus selectores QSS.
2. **Refactorización de `ASTCodeAuditor`**:
   - Incorporación de `_extract_strings` recursivo para evaluar ramas `body` y `orelse` de ternarios sin contaminar variables con las condiciones lógicas `test`.
   - Soporte para argumentos de rol/estado personalizados y componentes principales (`ModernButton`, `PlatformStatusCard`).
   - Resolución desacoplada de variables por tipo esperado (`role` vs `state`).
   - Detección de constantes en código frontend con exclusión explícita de `controls.py:_resolve_role_color`.
3. **Reporte y Salida del Terminal en Español**:
   - Salida del terminal, opciones de ayuda (`--help`), recomendaciones y banners completamente en español, alineado al estándar de herramientas del proyecto (`icon_manager.py`, `i18n_manager.py`).
   - Presentación obligatoria y prioritaria de roles y estados sin uso (`SIN USO`) con el archivo y la línea exacta (ejemplo: `frontend/common/theme.py:314`).
   - Estados de salida: `❌ [AUDITORÍA FALLIDA]`, `⚠️ [ADVERTENCIA DE AUDITORÍA]` y `✅ [APROBADO]`.
   - Incorporación de opciones `--unused`, `--missing` y `--strict` (código de salida 1 en caso de estilos muertos).

---

## 3. Verificación

Se ejecutó la suite de auditoría:
```powershell
uv run .\resources\tools\role_manager.py
```
Salida validada:
```text
================================================================================
 🎨  REPORTE DE AUDITORÍA DE ROLES Y ESTADOS QSS (MINIKICK)
================================================================================
🔹 Roles definidos en theme.py   : 63
🔹 Roles en uso en el frontend   : 63
🔹 Estados definidos en theme.py : 19
🔹 Estados en uso en el frontend : 19
--------------------------------------------------------------------------------
🔹 Roles faltantes (en código, NO en theme) : 0
🔹 Estados faltantes (en código, NO en theme): 0
🔸 Roles sin uso (en theme, NO en código)   : 0
🔸 Estados sin uso (en theme, NO en código)  : 0
================================================================================

--------------------------------------------------------------------------------
✅ [APROBADO] ¡Todos los roles y estados están perfectamente sincronizados! (Sin faltantes ni estilos sin uso)
================================================================================
```
