# Walkthrough: Control Multimedia Global de Música mediante Teclado y Hook Win32 de 64 Bits

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_05.md`  
**Módulos Involucrados:**
- `backend/workers/global_media_worker.py`
- `backend/workers/__init__.py`
- `backend/controllers/music_controller.py`
- `backend/core/main_window_core.py`
- `frontend/components/music/music_settings_panel.py`
- `frontend/views/music_view.py`
- `locales/en.json`
- `locales/es.json`
- `resources/tests/unit/workers/test_global_media_worker.py`

---

## 1. Resumen de Objetivos y Cambios

### A. Intercepción Global de Teclas Multimedia (`GlobalMediaWorker`)
- **Objetivo:** Permitir controlar la música (Play, Pause, Skip) usando los botones multimedia físicos del teclado incluso mientras se juega a pantalla completa, se transmite en OBS o con MiniKick minimizado en la bandeja del sistema.
- **Implementación:**
  - `QThread` dedicado (`Worker_Global_Media_Keys`) en `backend/workers/global_media_worker.py`.
  - Instalación de hook nativo de Windows `WH_KEYBOARD_LL` (13) con ciclo de mensajes Win32 no bloqueante (`GetMessageW`).
  - Configuración estricta de tipos ctypes compatibles con 64 bits (`HMODULE`, `DWORD`, `LPARAM`, `c_ssize_t`) en `kernel32.GetModuleHandleW` y `user32.SetWindowsHookExW`.
  - Captura de `VK_MEDIA_PLAY_PAUSE` (0xB3), `VK_MEDIA_NEXT_TRACK` (0xB0) y `VK_MEDIA_STOP` (0xB2).
  - Desmontaje limpio mediante `PostThreadMessageW(WM_QUIT)` y `UnhookWindowsHookEx`.

### B. Doble Cobertura con `WM_APPCOMMAND` y Atajos Qt
- En `MainWindowCore`, se implementó `nativeEvent` para capturar comandos de teclado/auriculares Bluetooth (`WM_APPCOMMAND`) y `keyPressEvent` para eventos locales de Qt.

### C. Control de Usuario e Internacionalización
- Interruptor interactivo **Teclas Multimedia Globales** incorporado en la pestaña de configuración del reproductor de música.
- Traducciones completas en español e inglés en `locales/es.json` y `locales/en.json`.

---

## 2. Verificación
- Pruebas unitarias en `resources/tests/unit/workers/test_global_media_worker.py` aprobadas con éxito en arranque, señales y ciclo de vida en vivo.
- Suite completa de 149 pruebas unitarias aprobadas al 100%.
