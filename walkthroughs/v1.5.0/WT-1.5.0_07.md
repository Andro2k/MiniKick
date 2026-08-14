# Walkthrough - WT-1.5.0_07: Corrección del Título de Notificaciones del Sistema Operativo Windows

## Resumen de Cambios

1. **Identificador de Aplicación de Windows (AppUserModelID)**:
   - En [`main.py`](file:///c:/Users/TheAn/Desktop/python/Kick/main.py), se reemplazó el identificador interno `"andro2k.minikick.app.1.5"` por el nombre de marca oficial `"MiniKick"`.
   - Esto hace que en las notificaciones del sistema emergentes de Windows (Action Center / System Tray) el encabezado muestre elegantemente **`MiniKick`** en lugar del ID técnico del ejecutable.

---

## Verificación

- **Pruebas Automatizadas (`pytest`)**: Ejecutado correctamente con 35 pruebas aprobadas.
- **Notificaciones del Sistema**: Encabezado en ventanas emergentes de Windows estilizado como `MiniKick`.
