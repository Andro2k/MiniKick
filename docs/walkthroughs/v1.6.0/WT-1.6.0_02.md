# Walkthrough v1.6.0_02: Herramienta de Automatización de Versiones y Ramas Git

Se ha creado e integrado la herramienta unificada de gestión y auditoría de Git en [git_manager.py](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/git_manager.py).

---

## 1. Novedades
- **Herramienta CLI y Menú Interactivo `git_manager.py`**:
  - Ubicada en `resources/tools/git_manager.py`, permite gestionar el ciclo de vida de versiones y ramas sin necesidad de recordar comandos complejos ni instalar herramientas de terceros.
  - Ofrece modos interactivos por menú (`python resources/tools/git_manager.py`) y ejecución directa por subcomandos (`audit`, `sync`, `start`, `cleanup`, `check`).
- **Capacidades Automatizadas**:
  - `audit`: Diagnóstico inmediato de coherencia de versión vs rama activa, estado del árbol de trabajo, commits pendientes y detección de ramas fusionadas obsoletas.
  - `start [vX.Y.Z]`: Automatiza la creación de ramas de release garantizando punto de partida limpio desde `main` actualizado, bumping de versión en [version.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/version.py) y push con tracking automático a GitHub.
  - `sync`: Poda de ramas remotas eliminadas (`git fetch -p`) y actualización de `main` en segundo plano.
  - `cleanup`: Detección y eliminación segura de ramas locales y remotas `release/*` ya integradas a `main`.
  - `check`: Ejecución de suite de tests y generación de la URL directa para abrir el Pull Request hacia `main` en GitHub.

---

## 2. Mejoras
- **Arquitectura Limpia y Cero Dependencias**: Implementado con separación estricta de responsabilidades (`GitRunner`, `VersionManager`, `GitAuditService`, `GitReleaseWorkflow`, `GitManagerCLI`), apoyándose exclusivamente en librerías estándar de Python y el binario nativo de Git.
- **Rendimiento $\mathcal{O}(1)$**: Consultas directas de divergencia y revisión de ancestros sin recorridos innecesarios de historial.

---

## 3. Correcciones
- Ninguna (nueva característica orientada a la productividad y gobernanza del repositorio).
