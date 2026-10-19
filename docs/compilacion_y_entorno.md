# Guía de compilación, entorno e instalación de MiniKick

Esta guía resume la preparación del entorno, la generación del instalador de Windows y los métodos de distribución para usuarios.

## 1. Preparar el entorno de desarrollo

```powershell
uv sync
```

Para abrir el administrador interactivo:

```powershell
uv run python .\resources\tools\build_manager.py
```

## 2. Compilar el ejecutable y el instalador

Instala Inno Setup 6 o 7 y ejecuta desde la raíz del repositorio:

```powershell
uv run python .\resources\tools\build_manager.py --package
```

El comando genera el ejecutable con PyInstaller y luego compila Inno Setup. El instalador versionado queda en `Output/MiniKick_Installer_v<VERSION>.exe`. Para compilar solo el instalador desde un ejecutable ya generado:

```powershell
uv run python .\resources\tools\build_manager.py --installer
```

El administrador busca `ISCC.exe` en `PATH` y en las ubicaciones comunes de Inno Setup 6/7. También se puede compilar directamente:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

## 3. Distribuir e instalar desde PowerShell

Publica `scripts/install.ps1` en la rama `main` y adjunta el instalador generado como asset de una release de GitHub. El comando de instalación interactiva será:

```powershell
irm https://raw.githubusercontent.com/Andro2k/MiniKick/main/scripts/install.ps1 | iex
```

El script consulta la última release, busca el instalador cuyo nombre coincide con la versión, descarga el asset, compara su SHA-256 con el digest de GitHub y solo entonces ejecuta el instalador. Si falta el asset o el digest, se detiene.

Para inspeccionar el script antes de ejecutarlo y usar instalación silenciosa:

```powershell
$installerScript = Join-Path $env:TEMP 'minikick-install.ps1'
Invoke-RestMethod https://raw.githubusercontent.com/Andro2k/MiniKick/main/scripts/install.ps1 -OutFile $installerScript
Get-Content $installerScript
& $installerScript -Silent
```

## 4. Distribuir mediante Winget

Winget requiere una release pública con URL HTTPS directa al instalador y SHA-256 correspondiente a esa versión. Después de publicar el asset, prepara y envía el manifiesto `Andro2k.MiniKick` al repositorio comunitario `microsoft/winget-pkgs`. El paquete se podrá instalar cuando el manifiesto pase la validación y el pull request sea aceptado:

```powershell
winget install --id Andro2k.MiniKick --exact
```

Cada release nueva necesita un manifiesto actualizado con la versión, URL y hash de ese instalador. No reutilices el hash de versiones anteriores.
