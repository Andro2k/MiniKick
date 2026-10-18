# Walkthrough: Herramienta de Automatización de Ramas y Versiones (`git_manager.py`)

Se ha creado e implementado la herramienta unificada de automatización en [git_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/git_manager.py).

---

## Características Implementadas

### 1. Modos de Uso
- **Menú interactivo con interfaz ANSI**:
  ```powershell
  python resources/tools/git_manager.py
  ```
- **Subcomandos por terminal**:
  ```powershell
  python resources/tools/git_manager.py audit
  python resources/tools/git_manager.py sync
  python resources/tools/git_manager.py start
  python resources/tools/git_manager.py start -v v1.7.0
  python resources/tools/git_manager.py cleanup
  python resources/tools/git_manager.py check
  ```

### 2. Arquitectura de Código
- `GitRunner`: Abstracción segura de comandos de Git con captura de errores y codificación UTF-8.
- `VersionManager`: Sincronización y bumping semántico con [version.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/version.py).
- `GitAuditService`: Chequeo de working tree, divergencia de `main` y detección de ramas ya fusionadas.
- `GitReleaseWorkflow`: Implementación de flujos de creación de ramas, poda y preparación de PR.
- `GitManagerCLI`: Interfaz interactiva para el desarrollador.

---

## Verificación
- Ejecutado `python resources/tools/git_manager.py audit` arrojando un diagnóstico 100% positivo del estado actual del repositorio:
  - Versión configurada: `v1.6.0`
  - Rama actual: `release/v1.6.0`
  - Coherencia: Rama coincide con versión.
  - Sincronización: `main` al día con `origin/main`.
  - Ramas obsoletas: Ninguna.
