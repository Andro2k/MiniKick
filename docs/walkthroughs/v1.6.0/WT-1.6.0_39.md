# Walkthrough WT-1.6.0_39: Suite Maestra de Control de Calidad (`system_health_audit.py`) y Modernización de Tooling

## Novedades

1. **Nueva Suite Maestra de Salud y Calidad ([`resources/tools/system_health_audit.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/system_health_audit.py))**:
   - Se diseñó y construyó un runner unificado que orquesta en un solo comando las 7 herramientas de auditoría del proyecto:
     1. **Icon Toolkit & Integrity** (`icon_manager.py`): 108 iconos en uso, 0 faltantes, 0 huérfanos, XML válido.
     2. **i18n Internationalization** (`i18n_manager.py`): 1239 claves, 100% paridad EN vs ES y placeholders.
     3. **Dead Code & Orphan Scanner** (`dead_code_manager.py`): 210 archivos escaneados, 0 símbolos huérfanos, 0 imports innecesarios.
     4. **QSS Role & State Auditor** (`role_manager.py`): 67 roles, 20 estados, 0 widget mismatches.
     5. **Unused Parameter Auditor** (`unused_parameter_manager.py`): 0 parámetros no referenciados.
     6. **Window & HWND Leak Auditor** (`window_audit_manager.py`): 12 vistas probadas, 0 micro-ventanas fantasma.
     7. **UI Flex & Responsive Matrix** (`ui_flex_inspector.py`): 12 vistas evaluadas de 1400px a 550px con 0 clipping.
   - **Dashboard Visual Consolidado**: Presenta un resumen estructurado en terminal con colores ANSI, tiempos de ejecución individuales y veredicto general.
   - **Soporte CLI / CI Desatendido**: Banderas `--all`, `--quick` (solo estáticos AST en < 6 segundos), `--json` (salida puramente parseable sin banners) y `--strict`.

2. **Verificación Pre-Flight en Build Manager ([`resources/tools/build_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/build_manager.py))**:
   - Se añadió la función `check_build_prerequisites` accesible mediante `--check` o `-c`.
   - Verifica la existencia y consistencia de `MiniKick.spec`, `version.py`, `version_info.txt`, `instalador.iss`, `pyproject.toml`, entorno `.venv`, assets e icono `assets/icons/icon.ico`.
   - Detección de binario generado previamente en `dist/` con cálculo de peso en Megabytes.

3. **Modos de Rendimiento y Presupuestos en Profiler ([`resources/tools/profiler_audit.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/profiler_audit.py))**:
   - Se incorporó CLI estructurado con `--quick`, `--full`, `--json` y `--strict`.
   - Evaluación automática contra presupuestos de rendimiento: RAM base $\le 180$ MB, throughput de spam $\ge 5,000$ msg/s, throughput de comandos $\ge 5,000$ msg/s y latencia de consultas SQLite $\le 5$ ms.

---

## Mejoras

1. **Modernización de [`resources/tools/git_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/git_manager.py)**:
   - Soporte para exportación diagnóstica en JSON con `--json` (rama actual, versión, divergencia con `origin/main` y ramas obsoletas fusionadas).
   - Bandera `--no-push` para ejecutar verificación completa de tests sin forzar subida remota de commits.
   - Modo desatendido con `sys.stdin.isatty()` que evita bloqueos en `input()` si se ejecuta en subprocesos o pipelines.

2. **Migración a `argparse` y Codificación UTF-8 en `build_manager.py`**:
   - Reemplazo del selector manual `sys.argv[1]` por `argparse` con formateo de ayuda y opciones (`--version-info`, `--check`, `--install-venv`, `--upgrade`, `--build`, `--all`, `--json`).
   - Reconfiguración explícita de `sys.stdout` y `sys.stderr` en UTF-8 para prevenir `UnicodeEncodeError` en consolas Windows (cp1252).

3. **Ejecución Aislada y Medición de Tiempos con `time.perf_counter()`**:
   - La suite maestra ejecuta cada herramienta en un proceso hijo independiente, garantizando aislamiento total de singletons de Qt (`QApplication`) y calculando la duración exacta por subsistema.
   - Adición del filtro `clean_ansi()` en el orquestador para eliminar secuencias de escape ANSI al comprobar expresiones de éxito.

---

## Correcciones

1. **Corrección de Ruta de Pruebas en `git_manager.py`**:
   - En `GitReleaseWorkflow.finish_check`, el comando de Pytest apuntaba a `resources/tests/frontend` (directorio histórico no existente tras la unificación de tests). Se actualizó a `resources/tests`, ejecutando correctamente los 76 tests de la suite completa.

2. **Corrección de Ruta de Icono en `build_manager.py`**:
   - La comprobación de prerrequisitos de assets buscaba `assets/icon.ico`. Se corrigió la ruta hacia la ubicación real del archivo especificada en `MiniKick.spec`: `assets/icons/icon.ico`.

3. **Sanitización de Salida JSON en `system_health_audit.py`**:
   - Se añadió el parámetro `silent` en `run_all` cuando se utiliza `--json`, asegurando que no se emitan líneas de progreso en stdout y el payload devuelto sea 100% JSON válido y parseable por herramientas de CI/CD.
