# Walkthrough Tecnico - MiniKick v1.6.5 (Paso 13)

Se incorporo un flujo de empaquetado reproducible y un instalador remoto de PowerShell para distribuciones publicadas en GitHub Releases.

---

## Novedades

- Se agrego `scripts/install.ps1`, que localiza el asset versionado de la release mas reciente, descarga el instalador de Windows y verifica su SHA-256 antes de ejecutarlo.
- El script permite instalacion interactiva por defecto y modo silencioso con `-Silent`.
- Se documento la distribucion por PowerShell y el proceso para solicitar la inclusion de MiniKick en el catalogo comunitario de Winget.

## Mejoras

- `build_manager.py` ofrece `--package` para compilar PyInstaller y luego Inno Setup, y `--installer` para compilar el instalador desde un `dist/MiniKick` existente.
- La deteccion de Inno Setup usa `PATH` y ubicaciones comunes de las versiones 6 y 7, en vez de depender de una ruta personal.
- La guia de compilacion ahora describe los comandos disponibles, el asset requerido para la instalacion remota y los requisitos del manifiesto Winget.

## Correcciones

- Se corrigio la guia de compilacion para que no atribuya al comando predeterminado del administrador de build una compilacion Inno Setup que no ejecutaba.
- La instalacion remota se detiene si el nombre/version del asset no coincide, si la URL no pertenece al repositorio esperado o si falta el digest SHA-256 verificable.
