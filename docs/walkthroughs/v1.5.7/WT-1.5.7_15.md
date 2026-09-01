# Walkthrough: Protección de Concurrencia y Ciclo de Vida en Worker_Fetch_Rewards_twitch

**Versión:** `v1.5.7`  
**Documento:** `WT-1.5.7_15.md`  
**Módulos Modificados:**
- [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
- [`backend/controllers/rewards_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py)

---

## 1. Resumen de Cambios

### A. Protección contra Múltiples Invocaciones Concurrente de `FetchRewardsWorker`
- En [`main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py#L921), se añadió verificación `isRunning()` antes de instanciar o iniciar un nuevo `FetchRewardsWorker` para Twitch en `_fetch_twitch_rewards()`.
- Esto previene la sobreescritura de la referencia y la destrucción prematura del hilo en segundo plano (`QThread: Destroyed while thread 'Worker_Fetch_Rewards_twitch' is still running`).

### B. Desacoplamiento de Afinidad de Hilos en Workers de Recompensas
- En [`rewards_controller.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/rewards_controller.py), se removió `parent=self` en la creación de `CreateRewardWorker` y `UpdateRewardWorker` para asegurar una gestión de ciclo de vida cooperativa y sin conflictos de afinidad de hilos Qt.

---

## 2. Verificación

```powershell
uv run pytest resources/tests/unit/providers/test_twitch_rewards.py resources/tests/unit/services/test_rewards_service.py -v
```
- **15/15 pruebas unitarias de recompensas aprobadas al 100%**.
