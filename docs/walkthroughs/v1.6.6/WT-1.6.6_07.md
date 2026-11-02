# Walkthrough Técnico — MiniKick v1.6.6 (Paso 07)

Corrección del coste de ~300 ms por visita a Settings y ajuste del arranque de la creación anticipada de vistas, a partir de `minikick_693577.log` (segunda sesión del archivo, 22:45) sobre el HEAD `c858b8c` de `release/v1.6.6`, que ya incluye los pasos 05 y 06. El desglose `[Perf/Integrations]` añadido en el paso 06 permitió medir la causa real y descartó la hipótesis del paso 05: el coste no estaba en el descifrado de tokens sino en el reparto del estado de plataformas a las vistas, donde tres de ellas reconstruían su tabla completa aunque el estado no hubiera cambiado. Módulos afectados: `frontend/views/commands_view.py`, `frontend/views/timers_view.py`, `frontend/views/rewards_view.py`, `frontend/views/alerts_view.py`, `frontend/main_window.py` y `resources/tests/test_connected_platforms_idempotence.py` (nuevo).

Validado con 16 pruebas nuevas (4 vistas × 4 casos), la batería relevante (125 pasan) y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos, parámetros sin uso, tokens de diseño, textos hardcodeados y señales Qt), todos en verde. El cambio se entrega como `0009-perf-idempotent-connected-platforms.patch` y aplica limpio sobre `c858b8c`. Se entrega además, como opcional, `0010-revert-token-decrypt-cache-OPCIONAL.patch` (ver «Corrección de la hipótesis del paso 05»).

---

## Diagnóstico a partir del log

| Medida (sesión 22:45) | Valor |
| --- | --- |
| Refresco de integraciones con 6 vistas creadas | 162.60 ms (`dashboard`=3.06, `settings_view`=0.00, `auth`=7.56, `views`=151.98) |
| Refresco de integraciones con todas las vistas creadas | 305.77 / 340.75 / 306.38 ms (`auth` 6.8–7.5 ms, `views` 294–330 ms) |
| Settings, revisita | `hooks` 318.81 ms (total 343.80 ms) |
| Primera visita de 7 vistas tras la creación anticipada | 24–46 ms (antes 85–282 ms) |
| Chat y Settings, primera visita | 580 ms y 400 ms (las abrió el usuario antes de que se anticiparan) |
| Triggers, revisita | 45–50 ms (`hooks` ≈ 23–27 ms: `_fetch_api_rewards`) |
| Resto de revisitas | 16–39 ms |

- **Causa del coste de Settings**: `_update_integrations_status_ui()` llama a `set_connected_platforms(...)` en todas las vistas que lo implementan. `CommandView` y `TimersView` ejecutan `populate_table(...)` y `RewardsView` ejecuta `_apply_filters()` en cada llamada, reconstruyendo tablas con widgets por celda aunque el diccionario de plataformas sea idéntico al anterior. Por eso `views` crece de ~152 a ~295 ms conforme existen más vistas, y se paga en cada visita a Settings (el hook la refresca siempre).
- **Descifrado de tokens**: `auth` mide ~7 ms por refresco (dos lecturas de tokens, Kick y Twitch). No era la causa.
- **Creación anticipada**: funciona. Las vistas que el usuario abrió después de ser anticipadas pasan a costar entre 24 y 46 ms en su primera visita. Las dos que quedaron fuera (Chat y Settings) las abrió el usuario antes de que el planificador llegara a ellas: el planificador esperaba 1500 ms tras la hidratación y el usuario abrió Chat unos 0.9 s después de ella.

## Novedades

- **Setters idempotentes en `CommandView`, `TimersView`, `RewardsView` y `AlertsView`**: `set_connected_platforms` compara el estado recibido con el almacenado y no hace nada si coinciden. Cada vista guarda su propia copia (`dict(...)`), de modo que una mutación posterior del diccionario del llamador no altera el estado de la vista. La garantía vive en la vista y no depende de quién la llame: sirve igual para el reparto de `MainWindowCore`, para la creación de la vista y para cualquier llamada futura.
- **Arranque más temprano de la creación anticipada**: `_PREWARM_START_DELAY_MS` pasa de 1500 a 300 ms. Con Chat como primera vista de la lista, en la sesión analizada se habría creado antes del primer clic del usuario.

## Mejoras

- **Efecto esperado en Settings**: `views` pasa de ~295–330 ms a ≈ 0 ms cuando el estado no cambia, y el `hooks` de Settings baja de ~300 ms a ~15 ms (`dashboard` ≈ 3 ms, `settings_view` ≈ 1 ms, `auth` ≈ 7 ms). La cifra es una estimación a partir del desglose del log; debe confirmarse con un log nuevo.
- **Separación de responsabilidades**: cada vista decide si necesita reconstruirse, en lugar de reconstruirse por cada notificación.
- **Sin cambios de comportamiento observable**: cuando el estado de plataformas cambia (conexión o desconexión), las vistas se actualizan exactamente igual que antes.

## Corrección de la hipótesis del paso 05

El paso 05 atribuyó el coste de Settings al descifrado DPAPI de tokens y añadió `0007-perf-token-decrypt-cache.patch`. La medición posterior (`auth` ≈ 7 ms) lo descarta como causa principal. Esa caché solo se justificaba por esa hipótesis y tiene un coste de seguridad: mantiene en memoria hasta 4 tokens en texto plano hasta el siguiente `save()` o `clear()`. No hay medición previa de `auth` sin la caché, por lo que su beneficio no está demostrado.

- **Recomendación**: revertirla. `0010-revert-token-decrypt-cache-OPCIONAL.patch` deshace exactamente `backend/database/encrypted_token_storage.py` y las 6 pruebas que se le añadieron en `test_encrypted_token_storage.py`; aplica tras `0009` (los archivos son disjuntos).
- **Si se prefiere conservarla**: no tiene efectos funcionales, solo el compromiso de retención descrito en el walkthrough del paso 05.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_connected_platforms_idempotence.py` | 16 pasan (sin reconstrucción con estado igual, reconstrucción con estado distinto, copia propia del estado, `None` tratado como vacío; para las 4 vistas) |
| Batería relevante (frontend, contratos, handlers, controladores, tokens, ajustes, auditores) | 125 pasan |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso, tokens de diseño, textos, señales Qt) | Sin hallazgos |

Las pruebas nuevas ejercitan los setters de las vistas reales sobre un sustituto ligero de `self`, sin instanciar widgets, por lo que no dependen de la pantalla del entorno.

**Fallos y limitaciones preexistentes, sin relación con este paso:**

- `test_giphy_and_tts_filter.py` (3 pruebas): dependen de la API key y de red de Giphy.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit`: intermitente (carrera entre `run()` y `stop()` con `channel_name=""`).
- La suite completa y las pruebas que instancian la ventana principal producen *segmentation fault* en el entorno de validación (Qt sin pantalla). El cambio de `_PREWARM_START_DELAY_MS` en `main_window.py` no tiene prueba automatizada; se valida con el siguiente log.

## Compromisos y riesgos a tener en cuenta

- **Arranque más temprano del planificador**: Chat (~540 ms de creación) se construye ahora 300 ms después de la hidratación, de modo que la ventana puede quedar ocupada ese tiempo justo tras mostrarse. Si el usuario interactúa en ese instante, esperará a que termine el fragmento.
- **Vistas con estado inicial por defecto**: `TimersView` y `RewardsView` inician con `{"kick": True, "twitch": True}`; el primer reparto real difiere de ese valor y se aplica con normalidad, por lo que no se omite ninguna actualización necesaria.

## Pendiente (no incluido en este paso)

- **Triggers**: `_fetch_api_rewards()` crea un cliente y lanza un worker de red en cada visita (≈ 23–27 ms de `hooks`). Es un refresco funcional; podría limitarse por antigüedad si se considera innecesario.
- **Settings, creación**: ~400 ms; conviene medir qué parte corresponde a la enumeración de dispositivos de audio.
- **Arranque y cierre**: trabajo previo al splash (~0.8 s tras los imports), hidratación de `integrations and profile` (~128 ms) y detención de workers (~1.1 s) que no se solapa por completo.
