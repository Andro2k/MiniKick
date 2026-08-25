# Walkthrough - Organización y Refactorización Estructural de MainWindowCore y AppContainer

Documento de referencia: `WT-1.5.3_03`  
Versión: `v1.5.3`  
Módulos modificados: `backend/core/main_window_core.py`, `backend/core/app_container_core.py`, `backend/services/__init__.py`

---

## 📋 Resumen

Se realizó una auditoría completa y reorganización estructural en [backend/core/main_window_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), [backend/core/app_container_core.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/app_container_core.py) y [backend/services/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/__init__.py), eliminando duplicidades, servicios obsoletos y métodos wrapper innecesarios en favor de una arquitectura limpia, mantenible y de alta cohesión (SRP/DRY).

---

## 🛠️ Elementos Refactorizados y Depurados

1. **Eliminación de Servicios Obsoletos**:
   - `MediaTriggerService` $\rightarrow$ Eliminado de `AppContainer` y del paquete `backend.services` (el audio y video se gestiona nativamente mediante `OverlayServerManager`).

2. **Eliminación de Alias Redundantes y Código Muerto**:
   - `self._nav_mapping` $\rightarrow$ Eliminado (la navegación utiliza `self._instantiated_views`).
   - `self.stream_schedule_storage` $\rightarrow$ Eliminado de `AppContainer` (se usa `self.schedule_storage`).
   - `self.stream_schedule_worker`, `self.stream_info_service`, `self.stream_info_controller`, `self.view_stream_info` $\rightarrow$ Eliminados en favor de los nombres unificados `schedule_worker`, `schedule_service`, `schedule_controller`, `view_schedule`.
   - `_handle_reauth_process()` $\rightarrow$ Eliminado (era un wrapper innecesario de una línea; se llama directamente a `_handle_auth_process()`).

3. **Organización Modular**:
   - Estructuración de `MainWindowCore` en 12 secciones lógicas bien delimitadas.
   - Estructuración de `AppContainer` por capas (Storage SQLite $\rightarrow$ Servicios $\rightarrow$ Auth $\rightarrow$ Overlays).
   - Verificación de la integridad de todos los imports y firmas.
