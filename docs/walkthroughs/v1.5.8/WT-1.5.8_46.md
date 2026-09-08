# Walkthrough - Corrección de Reconexión WebSocket en Rewards Overlay y Widgets OBS (v1.5.8_46)

## 1. Resumen y Objetivos

Se corrigió la falla por la cual el overlay de **rewards (puntos de canal)** (`assets/overlays/rewards/rewards.html`) dejaba de mostrar alertas y no se reconectaba automáticamente al cerrar y volver a abrir MiniKick, requiriendo recargar la fuente en OBS manualmente. Asimismo, se corrigió preventivamente el mismo temporizador defectuoso en los 7 widgets integrados en OBS.

---

## 2. Diagnóstico y Causa Raíz

### A. Deadlock en el Reintento de Reconexión de Rewards
- En `assets/overlays/rewards/rewards.html`, la función `scheduleReconnect()` utilizaba una variable booleana `isReconnecting = false`.
- Al desconectarse MiniKick, el socket emitía `ws.onclose`, fijando `isReconnecting = true` e iniciando un timer de 3 segundos hacia `connectWS()`.
- Cuando el socket intentaba conectar y MiniKick aún no estaba listo o el handshake fallaba, se disparaban `ws.onerror` y `ws.onclose`, que volvían a llamar a `scheduleReconnect()`.
- Sin embargo, `isReconnecting` **solo se restablecía a `false` dentro del callback `ws.onopen`**.
- Al haber fallado la conexión, `isReconnecting` permanecía perpetuamente en `true`, activando la cláusula de guarda `if (isReconnecting || reconnectTimer) return;`, lo que cancelaba definitivamente futuros reintentos de conexión.

### B. Puerto Fallback Heredado
- En `rewards.html` se utilizaba `localhost:6868` como fallback en caso de ausencia de `location.host`, cuando el puerto por defecto actual es `8090`.

### C. Temporizadores Colgados en Widgets OBS
- En los 7 widgets (`deaths.html`, `emote_combo.html`, `emote_explosion.html`, `pinned.html`, `poll.html`, `score.html`, `shoutout.html`), `scheduleReconnect()` no reseteaba `reconnectTimer = null` antes o durante la ejecución de `connectWS()`.
- Como resultado, tras el primer fallo de conexión, `reconnectTimer` retenía el handle entero del timer previo, causando que `if (!reconnectTimer)` no se cumpliera y detuviera la reconexión.

---

## 3. Modificaciones Implementadas

### A. [rewards.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/rewards/rewards.html)
1. **Eliminación de la bandera bloqueante**: Se removió `isReconnecting`.
2. **Reconexión Idempotente**:
   ```javascript
   function cleanupSocket() {
       stopHeartbeat();
       if (ws) {
           ws.onopen = null;
           ws.onmessage = null;
           ws.onerror = null;
           ws.onclose = null;
           try { ws.close(); } catch (e) { }
           ws = null;
       }
   }

   function scheduleReconnect() {
       cleanupSocket();
       if (reconnectTimer) clearTimeout(reconnectTimer);

       reconnectTimer = setTimeout(() => {
           reconnectTimer = null;
           console.log('[Rewards Overlay] Intentando reconectar WebSocket...');
           connectWS();
       }, RECONNECT_DELAY_MS);
   }
   ```
3. **Limpieza en Open**: En `ws.onopen`, se limpia y anula explícitamente cualquier `reconnectTimer` pendiente y se arranca el `heartbeat`.
4. **Actualización de Puerto Fallback**: Se cambió `'localhost:6868'` por `'localhost:8090'`.

### B. Widgets de OBS ([widgets/](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/))
Se actualizó `scheduleReconnect()` en los 7 archivos HTML de widgets:
- [deaths.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/deaths.html)
- [emote_combo.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/emote_combo.html)
- [emote_explosion.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/emote_explosion.html)
- [pinned.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/pinned.html)
- [poll.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/poll.html)
- [score.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/score.html)
- [shoutout.html](file:///c:/Users/TheAn/Desktop/python/Kick/assets/overlays/widgets/shoutout.html)

Patrón unificado y robusto aplicado:
```javascript
function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        connectWS();
    }, 3000);
}
```

---

## 4. Análisis de Rendimiento y Arquitectura (Big-O)

- **Complejidad Temporal**: $\mathcal{O}(1)$ por ciclo de desconexión / reintento.
- **Complejidad Espacial**: $\mathcal{O}(1)$ memoria constante. Se desvinculan todos los event listeners (`onopen`, `onmessage`, `onerror`, `onclose`) antes de cerrar la instancia de WebSocket, evitando fugas de memoria en el runtime Chromium de OBS Studio (CEF).
- **Resiliencia Continua**: Los overlays ahora reintentan la conexión indefinidamente en intervalos controlados de 3 segundos mientras MiniKick esté apagado, y se reconectan automáticamente tan pronto como la aplicación vuelve a iniciar sin requerir intervención del usuario.

---

## 5. Verificación y Resultados

- **Pruebas Automatizadas**:
  - `resources/tests/unit/core/test_diagnostic_telemetry.py` (5/5 PASSED)
  - `resources/tests/unit/ui/test_widget_controller.py` & `test_toast_and_widget_sync.py` (10/10 PASSED)
  - `resources/tests/unit/services/test_user_media_routes.py` (4/4 PASSED)
