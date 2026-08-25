# Walkthrough - Corrección de Conexión Independiente Kick & Twitch

Documento de referencia: `WT-1.5.3_02`  
Versión: `v1.5.3`  
Módulo modificado: `backend/core/main_window_core.py`

---

## 📋 Resumen del Problema

Cuando el autostart estaba deshabilitado y el usuario iniciaba la conexión de **Twitch** en primer lugar y luego iniciaba la conexión de **Kick**, el socket de Twitch se desconectaba o dejaba de recibir mensajes. Sin embargo, al iniciar primero Kick y luego Twitch, ambos funcionaban.

---

## 🔍 Causa Raíz

En `MainWindowCore`:
- Al presionar el botón de conectar Kick, `_handle_auth_process()` ejecutaba `_stop_connection_workers()`.
- El método `_stop_connection_workers()` contenía en su lista de parada tanto los workers de Kick (`Worker_Chat_Socket`, `Worker_Reward_Polling`, `Worker_Auth`, `Worker_Fetch_Rewards`, `Worker_Timers`) como los de Twitch (`Worker_Twitch_Chat_Socket`, `Worker_Twitch_Auth`).
- Por tanto, al conectar Kick, se terminaba abruptamente el worker `TwitchChatWorker` previamente iniciado y no se volvía a reconectar, dejando a Twitch inactivo.

---

## 🛠️ Solución Implementada

1. **Desacoplamiento y Alta Cohesión de Workers**:
   - Se dividió `_stop_connection_workers()` en dos métodos especializados y aislados:
     - `_stop_kick_connection_workers()`: Detiene exclusivamente los workers de Kick.
     - `_stop_twitch_connection_workers()`: Detiene exclusivamente los workers de Twitch.
   - `_stop_all_workers()` se mantiene para el cierre total de la aplicación (`_cleanup()`).
2. **Aislamiento en Procesos de Autenticación**:
   - `_handle_auth_process()` (Kick) ahora llama únicamente a `_stop_kick_connection_workers()`, preservando intacta cualquier sesión activa de Twitch.
   - `_handle_twitch_auth_process()` y `_handle_twitch_disconnect()` utilizan `_stop_twitch_connection_workers()`, asegurando que ninguna acción de Twitch interfiera con la conexión de Kick.
3. **Condicional de Notificación OAuth de Twitch**:
   - Se condicionó el toast informativo *"Abriendo inicio de sesión en el navegador..."* a `force=True` o `not is_authenticated()`. Si Twitch ya cuenta con tokens guardados en base de datos, se conecta directamente y solo muestra el toast de éxito *"Twitch Conectado"*.
