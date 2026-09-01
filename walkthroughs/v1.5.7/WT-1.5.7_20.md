# Walkthrough: Control Multimedia Global mediante Botones del Teclado

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_20.md`  
**Módulos Modificados / Creados:**
- [`backend/workers/global_media_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/global_media_worker.py) *(Nuevo)*
- [`backend/workers/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/__init__.py)
- [`backend/controllers/music_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py)
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
- [`frontend/components/music/music_settings_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/music_settings_panel.py)
- [`frontend/views/music_view.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/views/music_view.py)
- [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
- [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
- [`resources/tests/unit/workers/test_global_media_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/unit/workers/test_global_media_worker.py) *(Nuevo)*

---

## 1. Resumen de Cambios

### A. Worker de Teclas Multimedia Globales (`GlobalMediaWorker`)
- Creado en [`backend/workers/global_media_worker.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/workers/global_media_worker.py).
- Instala un hook de bajo nivel de Windows (`WH_KEYBOARD_LL`) en un hilo secundario independiente (`Worker_Global_Media_Keys`).
- Configuración de prototipos y tipos Win32 seguros para 64-bits (`HMODULE`, `DWORD`, `LPARAM`, `c_ssize_t`) en `kernel32.GetModuleHandleW`, `user32.SetWindowsHookExW` y `user32.CallNextHookEx`.
- Intercepta las pulsaciones de hardware a nivel de sistema operativo:
  - `VK_MEDIA_PLAY_PAUSE` (0xB3) / `VK_MEDIA_STOP` (0xB2) -> Pausar / Reanudar música.
  - `VK_MEDIA_NEXT_TRACK` (0xB0) -> Saltar a la siguiente canción en cola.
- Se desmonta limpiamente con `PostThreadMessageW(WM_QUIT)` y `UnhookWindowsHookEx` en el apagado.

### B. Integración con `MainWindowCore` y `MusicController`
- En [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), se integró el ciclo de vida del worker en el arranque y en `_stop_all_workers()`.
- Soporte adicional para mensajes de Windows `WM_APPCOMMAND` en `nativeEvent` y eventos de teclado locales de Qt (`keyPressEvent`).
- En [`music_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/music_controller.py), se añadió `handle_media_keys_toggle` para persistir la preferencia en `music_global_media_keys`.

### C. Configuración en la Interfaz de Usuario e Internacionalización
- En [`music_settings_panel.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/music/music_settings_panel.py), se añadió el switch interactivo **Teclas Multimedia Globales** en la pestaña de Configuración del reproductor de música.
- Traducciones completas agregadas a [`en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [`es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json).

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/ -q --tb=short
```
- **148/148 pruebas unitarias aprobadas al 100%**.
