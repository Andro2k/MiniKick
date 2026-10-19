# Guía de Compilación, Entorno y Empaquetado — MiniKick

Esta guía centraliza los procedimientos de configuración del entorno virtual de desarrollo y la compilación/empaquetado del ejecutable oficial de MiniKick.

---

## 1. Configuración del Entorno Virtual (Venv)

### Opción Recomendada (UV):
MiniKick utiliza `uv` como gestor de paquetes de alto rendimiento:

```powershell
# Sincronizar e instalar dependencias completas del lockfile
uv sync
```

### Opción Automatizada (Build Manager):
También puedes emplear el asistente interactivo de desarrollo:

```powershell
# Asistente de compilación y entorno
uv run python .\resources\tools\build_manager.py
```

---

## 2. Compilación del Ejecutable de MiniKick

### Opción Automatizada (Recomendada):
El gestor unificado se encarga de validar la versión semántica en `version.py`, actualizar `version_info.txt`, generar los artefactos de PyInstaller y compilar el instalador Inno Setup:

```powershell
uv run python .\resources\tools\build_manager.py
```

### Compilación Directa con PyInstaller:
Si requieres compilar únicamente los binarios sin generar el instalador:

```powershell
uv run pyinstaller --clean --noconfirm MiniKick.spec
```

Los binarios empaquetados se ubicarán en `dist/MiniKick/`.

---

## 3. Generación del Instalador (Inno Setup)

Para compilar el asistente de instalación final de Windows:

```powershell
# Compilar instalador con Inno Setup Compiler (ISCC)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss
```

El instalador compilado se generará en la carpeta `Output/`.

