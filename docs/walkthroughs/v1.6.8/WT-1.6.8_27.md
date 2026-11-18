# Walkthrough Técnico — MiniKick v1.6.8 (Paso 27)

Se alineó el instalador Inno Setup y el actualizador con el patrón de `sonorahq/sonora` (`sonora.iss`, `build-installer.ps1` e `install.rs`): la versión entra al compilador por parámetro, el relanzado tras una actualización silenciosa es explícito y la instalación deja un log recuperable.

---

## Contexto

- `build_manager.py` reescribía `#define MyAppVersion` dentro de `instalador.iss` con una regex, lo que ensuciaba el árbol de git en cada build.
- El `[Run]` con `postinstall` corría también en instalaciones silenciosas y el actualizador lanzaba el instalador solo con `/SILENT`.

## Mejoras

**Instalador (`scripts/installer/instalador.iss`)**
- `MyAppVersion` queda dentro de `#ifndef`: `ISCC /DMyAppVersion=<version>` tiene prioridad y el valor fijo solo sirve al compilar a mano.
- `[Run]`: "Abrir MiniKick" lleva `skipifsilent`; un segundo `[Run]` con `runasoriginaluser` y `Check: RelaunchRequested` reabre la app solo cuando el actualizador pasa `/relaunch=1`.
- `[Icons]`: el acceso directo del escritorio usa `Check: not SilentUpgrade`, así una actualización silenciosa no recrea un acceso directo que el usuario borró.

**Actualizador (`backend/services/updates/updater_service.py`)**
- `WindowsInstaller` lanza el instalador con `/SILENT /SUPPRESSMSGBOXES /NORESTART /LOG=... /relaunch=1`.
- La ruta del log (`%TEMP%\minikick_setup.log`) viaja por la variable de entorno `MINIKICK_SETUP_LOG`, igual que la ruta del instalador, sin interpolarse en el comando.

**Compilación (`resources/tools/build_manager.py`)**
- Se eliminó la reescritura del `.iss`; `compile_installer` pasa `/DMyAppVersion=<APP_VERSION>`, con `backend/config/version.py` como única fuente.

## Archivos afectados

- `scripts/installer/instalador.iss` (parche `0001`)
- `resources/tests/test_installer_script_paths.py` (parche `0001`)
- `backend/services/updates/updater_service.py` (parche `0002`)
- `resources/tools/build_manager.py` (parche `0002`)
- `resources/tests/test_windows_installer.py` (parche `0002`)
- `docs/walkthroughs/v1.6.8/WT-1.6.8_27.md` (parche `0003`)

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `pytest test_windows_installer.py test_installer_script_paths.py` | 6 aprobadas, 0 fallidas |
| `ruff check` sobre los archivos tocados | 3 errores S110 que ya existían (`whats_new_service.py`, `build_manager.py:14`); sin errores nuevos |
| `project_quality_suite.py --quick` | Sale con código 1 por 5 advertencias de `ModernButton` sin `parent`; son las mismas antes y después del cambio |
| Compilación real con `ISCC.exe` y prueba de actualización silenciosa | Pendiente: requiere Windows con Inno Setup 6 |

## Pendiente

- Probar en Windows: compilar con `python resources/tools/build_manager.py`, actualizar desde una versión anterior y revisar que MiniKick se reabra, que no se recree el acceso directo borrado y que exista `%TEMP%\minikick_setup.log`.
