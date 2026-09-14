# 🏗️ MiniKick — Recomendaciones de Arquitectura

> Análisis técnico del proyecto con base en la revisión del código fuente actual.
> Prioridad: Mantenibilidad · Escalabilidad · Principios SOLID · Eficiencia

---

## Resumen Ejecutivo

MiniKick tiene una arquitectura en capas bien definida (Controllers → Services → Database),
con buen uso de interfaces y workers de Qt. Sin embargo, hay **7 áreas de mejora clave**
detectadas que, de no atenderse, impactarán la mantenibilidad a medida que el proyecto escale.

---

## 🔴 1. `database/manager.py` — God Object

**Problema:** `DatabaseManager` tiene **858 líneas** mezclando:
- Creación y migración de tablas (`_create_tables`, `_upgrade_schema`)
- Índices y triggers SQL (`_create_indexes_and_views`)
- Lógica de analytics (`get_dashboard_analytics_summary`)
- Operaciones directas de dominio (`add_song_to_queue`, `log_spam_violation`, `save_channel_profile`)

Esto viola **SRP** y **SoR**. Un cambio en `music_queue` obliga a tocar la misma clase que gestiona el perfil del canal.

**Impacto:** O(n) en mantenibilidad — cada nuevo dominio engorda la misma clase.

**Solución propuesta:**

```
database/
├── manager.py              ← Solo: conexión, WAL, integridad, migración de esquema
├── schema/
│   ├── tables.py           ← CREATE TABLE separado por dominio
│   └── indexes.py          ← Índices y triggers
└── repositories/           ← [NUEVO] Un repositorio por dominio
    ├── music_repository.py
    ├── spam_repository.py
    ├── command_repository.py
    └── analytics_repository.py
```

**Big-O ganado:** `DatabaseManager` pasa de O(n_dominios) a O(1) — solo gestiona infraestructura de conexión.

---

## 🔴 2. `services/chat/chat_service.py` — Mezcla de responsabilidades

**Problema:** Una sola clase gestiona:
- Configuración de TTS (provider, volume, speed, voice, synthesis params)
- Configuración del overlay del chat (theme, size, fade, bots)
- Persistencia directa a `settings_storage`
- Síntesis de voz en tiempo real (`speak`, `stop_tts`)

Son **4 responsabilidades distintas**. Si el overlay cambia de tecnología, hay que tocar la misma clase que maneja voces Piper.

**Solución propuesta:**

```
services/chat/
├── tts_settings_service.py    ← [NUEVO] get/save TTS config, set_provider, set_voice
├── chat_overlay_service.py    ← [NUEVO] get/save overlay settings
├── tts_service.py             ← Solo: speak, stop, warm_up (sin persistencia propia)
└── chat_service.py            ← Orquestador liviano que delega en los anteriores
```

---

## ⚠️ 3. `core/app_container_core.py` — Constructor Dios

**Problema:** El `__init__` instancia **15+ dependencias** en secuencia mezclando capas. Un fallo intermedio no es rastreable.

**Solución propuesta:** Dividir en factory methods semánticos:

```python
class AppContainerCore:
    def __init__(self):
        self._storage  = self._build_storage_layer()
        self._services = self._build_service_layer(self._storage)
        self._auth     = self._build_auth_layer(self._storage, self._services)
        self._overlay  = self._build_overlay_layer(self._storage, self._services)

    def _build_storage_layer(self) -> StorageBundle: ...
    def _build_service_layer(self, s: StorageBundle) -> ServiceBundle: ...
    def _build_auth_layer(self, s, sv) -> AuthBundle: ...
    def _build_overlay_layer(self, s, sv) -> OverlayBundle: ...
```

**Ganancia:** Cada capa es testeable de forma aislada.

---

## ⚠️ 4. `interfaces/` — Nomenclatura Inconsistente

**Problema:** El directorio mezcla convenciones:

| Archivo actual | Problema |
|---|---|
| `alert_interfaces.py` | sufijo `_interfaces` (plural) |
| `auth_interfaces.py` | sufijo `_interfaces` (plural) |
| `chat_provider.py` | sin sufijo, nombre del concepto |
| `chat_service.py` | colisiona con `services/chat/chat_service.py` |
| `music_provider.py` | sin sufijo |
| `tts_interfaces.py` | sufijo `_interfaces` (plural) |

**Solución propuesta:** Prefijo `i_` uniforme para todas las interfaces:

```
interfaces/
├── i_alert.py
├── i_auth.py
├── i_browser.py
├── i_chat_provider.py
├── i_chat_service.py
├── i_music_provider.py
├── i_settings.py
├── i_tts.py
└── i_updater.py
```

---

## ⚠️ 5. `models/` — Capa de Dominio Incompleta

**Problema:** Solo existe `alert_models.py`. El resto de dominios circula como `dict` entre capas, perdiendo seguridad de tipos.

**Evidencia** en `alerts_controller.py`:
```python
# Duck-typing frágil — no hay garantía de qué contiene `cfg`
plat = key[0] if isinstance(key, tuple) else getattr(cfg, "platform", None)
```

**Solución propuesta:**

```
models/
├── alert_models.py      ← Ya existe ✅
├── command_models.py    ← [NUEVO] CommandDTO, CommandPermission(Enum)
├── reward_models.py     ← [NUEVO] RewardDTO, RewardConfig
├── schedule_models.py   ← [NUEVO] ScheduleEntry, Platform(Enum)
├── timer_models.py      ← [NUEVO] TimerDTO
├── spam_models.py       ← [NUEVO] SpamFilter, SpamPenalty(Enum)
└── widget_models.py     ← [NUEVO] WidgetConfig
```

**Big-O ganado:** La validación en controllers pasa de O(n_checks) con `getattr`/`isinstance` a O(1) — el tipo garantiza los campos.

---

## ⚠️ 6. `controllers/` — Duck-Typing que rompe encapsulamiento

**Problema** en `alerts_controller.py`:
```python
# El controller accede al storage INTERNO del service — viola Dependency Inversion
if configs is None and hasattr(self.service, "storage") and hasattr(self.service.storage, "load_all"):
    configs = self.service.storage.load_all()
```

**Solución:** El contrato de interfaz debe ser explícito y el controller no debe conocer el storage:

```python
# interfaces/i_alert_service.py
class IAlertService(Protocol):
    def load_all_configs(self) -> dict[tuple[str, str], AlertConfig]: ...
    def save_config(self, config: AlertConfig) -> None: ...
    def trigger_test_alert(self, platform: str, alert_type: str) -> None: ...
```

---

## 🔵 7. Sistema de ErrorCode

**Problema:** Los errores se propagan como strings planos:
```python
# workers/kick_chat_worker.py
self.error_occurred.emit(str(e))
```
El receptor no puede manejarlos programáticamente (ej. reconectar en `CONNECTION_LOST` vs toast en `AUTH_EXPIRED`).

**Solución propuesta:**

```python
# backend/models/result.py
from enum import Enum
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")

class ErrorCode(Enum):
    AUTH_EXPIRED       = "AUTH_EXPIRED"
    CONNECTION_LOST    = "CONNECTION_LOST"
    ROOM_ID_NOT_FOUND  = "ROOM_ID_NOT_FOUND"
    STORAGE_ERROR      = "STORAGE_ERROR"

@dataclass
class Result(Generic[T]):
    ok: bool
    value: T | None = None
    error: ErrorCode | None = None
    detail: str = ""
```

---

## 🔵 8. `frontend/widgets/` — Colisión de nombres

**Problema:** `frontend/widgets/` contiene primitivas de UI (`blocks.py`, `controls.py`, `table.py`) pero comparte nombre con la feature de "stream widgets" (`widgets_view.py`, `widget_service.py`, `components/widgets/`). Genera confusión al navegar.

**Solución:** Renombrar `frontend/widgets/` → `frontend/ui_primitives/` o `frontend/base_widgets/`.

---

## 📊 Resumen y Orden de Ejecución Recomendado

| # | Área | Severidad | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | `DatabaseManager` God Object | 🔴 Crítico | Alto | Muy alto |
| 2 | `ChatService` mezcla responsabilidades | 🔴 Crítico | Medio | Alto |
| 3 | `AppContainerCore` constructor | ⚠️ Importante | Bajo | Alto |
| 4 | `interfaces/` nomenclatura | ⚠️ Importante | Bajo | Medio |
| 5 | `models/` incompletos | ⚠️ Importante | Medio | Alto |
| 6 | Duck-typing en controllers | ⚠️ Importante | Bajo | Medio |
| 7 | Sistema de ErrorCode | 🔵 Mejora | Medio | Medio |
| 8 | `widgets/` naming collision | 🔵 Mejora | Bajo | Bajo |

> **Orden de ejecución recomendado:**
> **#4** (nomenclatura — bajo riesgo, alta claridad) →
> **#5** (modelos — habilita las demás mejoras) →
> **#6** (controllers — usa modelos recién creados) →
> **#2** (ChatService split) →
> **#1** (DatabaseManager refactor) →
> **#3** y **#7**
