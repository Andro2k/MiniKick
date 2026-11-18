# Walkthrough Técnico — MiniKick v1.6.8 (Paso 25)

Se corrigió el icono que no aparecía en la barra de tareas durante la actualización. El actualizador lanza el instalador con `/SILENT` y su ventana mostraba un icono genérico porque `assets/icons/icon.ico` solo contenía los tamaños 16, 32, 48, 64 y 128 px, sin 256 px ni los intermedios (20, 24, 40) que Windows usa para la barra de tareas.

---

## Correcciones

- `icon.ico` se regeneró desde `assets/icons/common/logo.svg` con 9 tamaños (16, 20, 24, 32, 40, 48, 64, 128 y 256 px): BMP hasta 64 px y PNG en 128 y 256 px.
- El icono del instalador (`SetupIconFile`) y el del ejecutable (`MiniKick.spec`) usan el mismo archivo, por lo que ambos quedan corregidos sin cambios de código.

## Archivos afectados

- `assets/icons/icon.ico` (parche `0001`).

## Verificación

| Comprobación | Resultado |
| --- | --- |
| Lectura del `.ico` con Pillow | 9 tamaños, incluido 256 px |
| `git am` del parche 0001 sobre un clon limpio de `release/v1.6.8` | Aplica sin conflictos |
| Prueba visual en Windows (barra de tareas del instalador) | Pendiente: requiere recompilar con PyInstaller e Inno Setup |
