# Walkthrough: Corrección del Flujo Pasivo de Autenticación de Kick y Módulo de Rewards

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_07.md`  
**Módulos Involucrados:**
- `backend/services/auth/oauth_service.py`
- `backend/workers/kick_auth_worker.py`
- `backend/core/main_window_core.py`
- `backend/controllers/rewards_controller.py`
- `resources/tests/unit/providers/test_kick_auth.py`

---

## 1. Resumen de la Corrección

### A. Desacoplamiento de `get_tokens()` vs `login()` en `AuthManager`
- **Comportamiento Pasivo y Seguro**:
  El método `AuthManager.get_tokens(force=False)` ahora retorna `{}` si no existen tokens guardados en disco, en lugar de disparar pasivamente el flujo interactivo `_new_login()` que abría el navegador y ocupaba el puerto local 8080.
- **Método `login()` Explícito**:
  Se implementó el método `AuthManager.login(force=False)` como el único punto de entrada autorizado para solicitar al usuario que inicie sesión mediante el navegador si no se cuenta con credenciales activas.
- **Refresco Seguro de Token**:
  En `AuthManager.refresh_token()`, si no existe `refresh_token` o ocurre un error de red durante la renovación, se retorna `{}` sin invocar el inicio de sesión forzado.

### B. Worker de Autenticación (`KickAuthWorker`)
- `KickAuthWorker.run()` ahora invoca explícitamente `self.auth_manager.login(force=self.force)`.

### C. Navegación a Rewards y Consultas Seguras (`is_authenticated`)
- En `MainWindowCore._fetch_api_rewards()`, se reemplazó la consulta ambigua `if self.auth_manager.get_tokens():` por `if self.auth_manager.is_authenticated():`.
- En `RewardsController._handle_add()` y `_handle_edit()`, se validan las credenciales con `is_authenticated()`, evitando que al entrar al módulo de Rewards o crear recompensas locales sin cuenta vinculada se lance el navegador.

---

## 2. Verificación
- Creada suite unitaria `resources/tests/unit/providers/test_kick_auth.py` (5 pruebas unitarias verificando llamadas pasivas sin disparar `_new_login`).
- Suite completa de pruebas ejecutada: **157 / 157 aprobadas al 100%**.
