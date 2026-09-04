# Walkthrough v1.5.8_17: Corrección de 'Internal C++ object already deleted' y Guardias Seguras de QThread

## 1. Resumen Ejecutivo
Se resolvió la excepción fatal `RuntimeError: libshiboken: Internal C++ object (TwitchAuthWorker) already deleted`, que se manifestaba cuando el usuario autenticaba una plataforma y luego intentaba conectar la otra. Se introdujo una utilidad estática `MainWindowCore._is_worker_running` a prueba de objetos Shiboken/C++ recolectados, y se aseguraron los ciclos de vida de los workers de autenticación y de recompensas mediante auto-limpieza al emitirse la señal `finished`.

---

## 2. Diagnóstico Técnico

### Causa Raíz
1. Cuando un `QThread` (como `TwitchAuthWorker` o `KickAuthWorker`) finaliza, su señal `finished` ejecuta `deleteLater()`.
2. `deleteLater()` destruye el objeto nativo en C++.
3. En Python, la referencia de instancia (`self.twitch_auth_worker`) continúa existiendo y no es `None`, pero su objeto C++ ya fue liberado.
4. Al evaluar `if self.twitch_auth_worker and self.twitch_auth_worker.isRunning():`, Shiboken detecta que el puntero C++ subyacente es nulo y lanza un `RuntimeError` no recuperable que derribaba el hilo principal.

---

## 3. Cambios Implementados

### A. Helper Seguro de QThread (`backend/core/main_window_core.py`)
Se implementó el método seguro `_is_worker_running`:
```python
@staticmethod
def _is_worker_running(worker) -> bool:
    if worker is None:
        return False
    try:
        return bool(worker.isRunning())
    except (RuntimeError, AttributeError):
        return False
```
Si el objeto de C++ fue destruido, la excepción `RuntimeError` es neutralizada y la función retorna de forma segura `False`.

### B. Auto-Limpieza de Punteros en `finished`
Se conectó la señal `finished` de los workers de autenticación y de recompensas para restablecer a `None` su correspondiente atributo:
- `self.kick_auth_worker.finished.connect(lambda: setattr(self, 'kick_auth_worker', None))`
- `self.twitch_auth_worker.finished.connect(lambda: setattr(self, 'twitch_auth_worker', None))`
- `self.fetch_rewards_worker.finished.connect(lambda: setattr(self, 'fetch_rewards_worker', None))`
- `self.fetch_twitch_rewards_worker.finished.connect(lambda: setattr(self, 'fetch_twitch_rewards_worker', None))`
- Limpieza explícita `self.twitch_auth_worker = None` en `_on_twitch_auth_success`.

### C. Pruebas Unitarias (`resources/tests/unit/core/test_logging.py`)
Se añadió `test_is_worker_running_safety`:
- Valida que `_is_worker_running(None)` retorne `False`.
- Valida que un worker activo retorne `True`.
- Valida que un worker cuyo C++ object arroje `RuntimeError` sea neutralizado y retorne `False` sin propagar error.

---

## 4. Verificación y Resultados
```bash
.venv\Scripts\python -m pytest resources/tests/unit
# Resultado: 239 passed in 12.60s (100% exitoso)
```
