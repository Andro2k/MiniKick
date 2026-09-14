# WT-1.5.9_03: Calibración y Auditoría de Iconos en `icon_manager.py`

- **Versión**: v1.5.9
- **Tipo**: Tooling Refactor & Integrity Calibration
- **Componentes**:
  - [`resources/tools/icon_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/icon_manager.py)
  - [`resources/tests/unit/ui/test_frontend_common.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_frontend_common.py)
  - [`resources/tests/unit/ui/test_icons_integrity.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_icons_integrity.py)

---

## 1. Descripción del Problema

Al ejecutar la herramienta [`icon_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/icon_manager.py) (Opción 1: *Auditar iconos sin uso*), el icono `message.svg` no figuraba en la lista de iconos huérfanos a pesar de que ya no se utilizaba en ningún lugar del código de producción de la aplicación. En su lugar, el reporte indicaba únicamente 8 iconos sin uso en vez de los 12 reales.

### Causas Raíz Identificadas:
1. **Contaminación por pruebas unitarias**: La herramienta ejecutaba un escaneo recursivo general desde `BASE_DIR` sin aislar la carpeta `resources/tests/`. En [`test_frontend_common.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_frontend_common.py) existían llamadas simuladas como `sidebar.add_tab("Chat", "message.svg")`, `alert-circle.svg` y `refresh.svg`, haciendo que la herramienta creyera falsamente que estaban en uso en la aplicación.
2. **Escaneo indiscriminado de extensiones**: La inclusión de archivos `.json` forzaba a la herramienta a inspeccionar backups masivos (de más de 690 KB) y archivos de traducción sin contener referencias a iconos.
3. **Fragmentos de f-strings y extensiones aisladas**: Cadenas como `f"{stem}_{clean_hex}.svg"` en [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) o verificaciones de sufijo como `endswith(".svg")` producían falsos positivos de iconos faltantes con nombre `'.svg'`.
4. **Hacks residuales**: Existía un conjunto `MOCK_TEST_ICONS = {"non_existent_icon_xyz_123.svg"}` para sortear fallos provocados por el escaneo de tests.

---

## 2. Solución Aplicada

### 2.1. Delimitación Estricta de Directorios de Aplicación
- Se configuró el escáner para inspeccionar por defecto únicamente el código fuente de producción: `DEFAULT_TARGET_DIRS = ["frontend", "backend"]` y `DEFAULT_TARGET_FILES = ["main.py"]`.
- Se amplió `IGNORED_DIRS` para excluir `.venv`, `__pycache__`, `.git`, `.pytest_cache`, `.agents`, `resources`, `docs`, `locales`, `assets`, `scratch`, `build`, `dist`.
- Se añadió el flag opcional `--include-tests` para permitir auditar la suite de pruebas bajo demanda.

### 2.2. Motor de Extracción AST (`IconASTVisitor`)
- Implementación de un visitor `ast.NodeVisitor` que:
  - Omite docstrings de módulos, clases y funciones (evitando falsos positivos por ejemplos en documentación).
  - Omite fragmentos constantes dentro de f-strings (`ast.JoinedStr`), ignorando plantillas dinámicas como `f"{stem}_{clean_hex}.svg"`.
  - Verifica que el nombre del icono contenga una raíz (`stem`) no vacía antes de la extensión `.svg`, descartando literales sueltos como `".svg"`.
- Fallback automático mediante expresiones regulares optimizadas para archivos no Python (como `.qss`).

### 2.3. Actualización de Iconos en Tests Unitarios
- Se actualizaron las referencias de mock en [`test_frontend_common.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/ui/test_frontend_common.py) para que utilicen los iconos activos del sistema (`refresh-duotone.svg`, `dialog-duotone.svg`, `megaphone-filled.svg`).
- Se eliminó el hack `MOCK_TEST_ICONS` de `icon_manager.py`.

### 2.4. CLI Completa y Salida Profesional en Español
- Se incorporaron argumentos completos vía `argparse`:
  - `--audit`: Auditoría completa (sin uso y faltantes).
  - `--unused`: Reporte de iconos sin uso con peso en disco y bytes recuperables.
  - `--missing`: Reporte de iconos faltantes (retorna código de salida 1 si existen faltantes).
  - `--report`: Reporte detallado de ocurrencias y rutas por icono.
  - `--clean`: Limpieza interactiva con confirmación segura `(s/N)`.
  - `--force`: Limpieza directa no interactiva.
  - `--strict`: Falla (exit code 1) ante cualquier icono faltante o sin uso (ideal para CI/CD).
  - `--json`: Exportación estructurada en JSON.

---

## 3. Verificación de Resultados

### 3.1. Auditoría de Iconos Sin Uso (`--unused`)
```powershell
uv run python resources/tools/icon_manager.py --unused
```
**Salida obtenida:**
```text
=======================================================
 AUDITORÍA DE ICONOS SIN USO (SOBRANTES)
=======================================================
📊 Total de iconos en assets/icons: 107
✅ Iconos en uso en el código: 95
🟡 Iconos SIN USO detectados: 12

📋 Lista de Iconos Sin Uso (pueden ser eliminados si no se planea usarlos):
  [X] alert-circle.svg               (  408 bytes)
  [X] clipboard-text.svg             (  714 bytes)
  [X] hash.svg                       (  788 bytes)
  [X] message.svg                    (  493 bytes)
  [X] minimize.svg                   (  886 bytes)
  [X] music.svg                      (  325 bytes)
  [X] player-pause.svg               (  297 bytes)
  [X] player-play.svg                (  270 bytes)
  [X] player-skip.svg                (  325 bytes)
  [X] refresh.svg                    (  309 bytes)
  [X] restore.svg                    (  324 bytes)
  [X] text-size.svg                  (  726 bytes)

💾 Espacio total recuperable: 5,865 bytes (~5.7 KB)
```
> [!NOTE]
> `message.svg` ahora se detecta de forma inmediata y precisa junto con los otros 11 iconos huérfanos.

### 3.2. Auditoría de Iconos Faltantes (`--missing`)
```powershell
uv run python resources/tools/icon_manager.py --missing
```
**Salida obtenida:**
```text
=======================================================
 AUDITORÍA DE ICONOS FALTANTES (USADOS EN CÓDIGO)
=======================================================
🔴 Iconos faltantes detectados: 0

✅ ¡Perfecto! Todos los iconos referenciados en el código existen físicamente en disco.
```

### 3.3. Suite de Pruebas Unitarias
```powershell
uv run pytest resources/tests/unit/ui/test_icons_integrity.py resources/tests/unit/ui/test_frontend_common.py
```
**Resultado:**
- `test_icons_integrity.py`: 2/2 PASSED
- `test_frontend_common.py`: 13/13 PASSED

---

## 4. Eficiencia Big-O

- **Complejidad de Tiempo**: Reducida a $\mathcal{O}(N)$ donde $N$ es el total de tokens en archivos de código real (`frontend/`, `backend/`, `main.py`). Se eliminó la lectura y parseo innecesario de archivos de respaldo JSON de gran tamaño (>690 KB) y archivos no relacionados.
- **Complejidad de Espacio**: $\mathcal{O}(M)$ en memoria donde $M$ es el conjunto de cadenas de iconos únicos (~107 elementos), logrando consultas y cruces en $\mathcal{O}(1)$ mediante conjuntos nativos (`set`).
