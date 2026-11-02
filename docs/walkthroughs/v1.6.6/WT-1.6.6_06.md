# Walkthrough Técnico — MiniKick v1.6.6 (Paso 06)

Creación anticipada de vistas en tiempo ocioso y medición del refresco de integraciones, a partir del análisis de `minikick_fed150.log` sobre el HEAD `6745bf3` de `release/v1.6.6`. Tras la caché de ajustes del paso anterior, el log muestra que el lag al navegar rápido ya no está en las revisitas (todas ≤ 36 ms salvo Settings y Triggers) sino en la primera visita a cada módulo, donde la creación perezosa de la vista cuesta entre 78 y 560 ms en el hilo principal. Este paso traslada esa creación al tiempo ocioso posterior al arranque y añade un desglose que permitirá localizar con datos el coste de ~300 ms que sigue cargando Settings. Módulos afectados: `frontend/view_prewarmer.py` (nuevo), `frontend/main_window.py` y `resources/tests/test_view_prewarmer.py` (nuevo).

Validado con 6 pruebas nuevas del planificador (`test_view_prewarmer.py`), la batería de pruebas relevante (97 pasan) y los auditores del proyecto (fronteras de arquitectura, DRY, código muerto, ubicación de archivos, parámetros sin uso, tokens de diseño, textos hardcodeados y ciclo de vida de señales Qt), todos en verde. El cambio se entrega como `0008-perf-view-prewarm-integrations-timing.patch` y aplica limpio sobre `6745bf3`, con o sin `0007-perf-token-decrypt-cache.patch`.

---

## Diagnóstico a partir del log

| Medida (`minikick_fed150.log`) | Valor |
| --- | --- |
| Primera visita, `create` (Chat / Settings / Alerts / Triggers) | 560 / 453 / 256 / 244 ms |
| Primera visita, `create` (Stream Info / Comandos / Music) | 225 / 210 / 209 ms |
| Primera visita, `create` (Widgets / Timers) | 96 / 78 ms |
| Suma de las creaciones perezosas | ≈ 2.3 s en el hilo principal |
| Revisitas (todas las vistas salvo Settings y Triggers) | 14–36 ms |
| Triggers, revisita | 46–58 ms (`hooks` ≈ 27 ms: `_fetch_api_rewards`) |
| Settings, revisita | 307–315 ms (`hooks` 289–300 ms) |
| Bootstrap total | 1912 ms |

- **Primera visita**: cada módulo se construye al abrirlo por primera vez. Quien recorre la barra lateral rápido paga esos costes uno detrás de otro, y es la causa dominante del lag que queda.
- **Settings**: sigue en ~300 ms por visita y el coste está en `hooks` (`_update_integrations_status_ui()`), no en el montaje. El HEAD `6745bf3` **no incluye** `0007-perf-token-decrypt-cache.patch` (la caché de descifrado DPAPI), por lo que este log no valida ni refuta esa hipótesis; solo confirma que Settings sigue siendo el único valor atípico en las revisitas.

## Novedades

- **`ViewPrewarmer`** (`frontend/view_prewarmer.py`): planificador que crea las vistas pendientes de una en una cuando la aplicación está ociosa. No depende de Qt: recibe por inyección la función de creación, la lista de vistas, los predicados `is_created` / `is_active`, la antigüedad de la última navegación y el planificador (`QTimer.singleShot` en producción, una cola falsa en las pruebas). Se detiene cuando la ventana se está cerrando y aísla las excepciones: si una vista falla, se registra un aviso y continúa con las demás.
- **Creación anticipada en `MainWindowCore`**: se programa desde `_schedule_startup_followups()`, 1500 ms después de terminar la hidratación inicial. La lista de vistas se deriva de `_NAV_CONFIG` excluyendo `Dashboard` (ya creada) y `Developer`, de modo que no hay una segunda lista que mantener. Orden: el de la barra lateral.
- **Cesión a la interacción del usuario**: `_handle_navigation` registra el instante de la última navegación; si hubo una hace menos de 600 ms, el planificador aplaza el siguiente paso 600 ms en lugar de bloquear el hilo justo mientras el usuario se mueve.
- **Registro de cada paso**: `[Perf/Prewarm] View 'X' prewarmed in N ms` y `[Perf/Prewarm] All views are ready.`
- **Desglose de `_update_integrations_status_ui()`**: cuando el refresco supera 50 ms (`_SLOW_STATUS_REFRESH_MS`) se registra `[Perf/Integrations] Status refresh took N ms (dashboard=…, settings_view=…, auth=…, views=…)`. `auth` corresponde a `get_connected_platforms()`, es decir, a las dos lecturas de tokens de Kick y Twitch.

## Mejoras

- **Separación de responsabilidades y DIP**: la política de «cuándo y en qué orden» crear vistas vive en una clase propia, probada sin Qt, y la ventana principal solo aporta los hechos (qué existe, si se cierra, cuándo navegó el usuario).
- **Una sola fuente de verdad** para el orden y el conjunto de vistas (`_NAV_CONFIG`).
- **Efecto esperado en la primera visita**: si la creación anticipada ha terminado, `create` baja de 78–560 ms a ~10–25 ms, el coste que ya se observa en las revisitas. La creación total (~2.3 s) pasa a ejecutarse en fragmentos de 78 a 560 ms durante los segundos posteriores al arranque, con 150 ms de margen entre fragmentos. Esta cifra es una estimación a partir del log; debe confirmarse con un log nuevo.

## Compromisos y riesgos a tener en cuenta

- **Hilo principal ocupado tras el arranque**: la creación de widgets debe hacerse en el hilo de la interfaz. Cada fragmento bloquea el bucle de eventos entre 78 y 560 ms (Chat es el mayor). El planificador evita empezar un fragmento si el usuario acaba de navegar, pero un clic que llegue durante un fragmento esperará hasta que termine.
- **Memoria**: todas las vistas quedan residentes, algo que ya ocurría tras visitarlas.
- **Efectos de creación que se adelantan**: cualquier trabajo que una vista haga al construirse (por ejemplo, Alerts consulta `get_connected_platforms()`) ocurre ahora en tiempo ocioso en lugar de en la primera visita.
- **Sin cambios de comportamiento** en navegación, ganchos por vista ni señales: si el usuario abre una vista antes de que se anticipe, se crea como siempre.

## Revisión previa de los cambios de frontend (commits `0dd554d`, `15793e8`, `d55fce9`)

- Rediseño de ajustes: `BaseView` admite una columna de contenido centrada (`max_content_width` / `min_content_width`), `SettingRow` y `SliderRow` aceptan roles de título y descripción, y `Size.CONTENT_MAX_WIDTH` / `CONTENT_MIN_WIDTH` y el rol QSS `setting_title` están definidos en el tema.
- 97 pruebas relevantes pasan, incluidas las nuevas `test_centered_view_layout.py` y `test_chat_voice_rows.py`. Los auditores de diseño, textos, roles y estados QSS, señales Qt, traducciones, iconos y código muerto no reportan hallazgos, y no quedan referencias a los iconos eliminados.
- **Observación**: la columna centrada fija un mínimo de 520 px con barra de desplazamiento horizontal desactivada; si la ventana pudiera ser más estrecha que ese mínimo más los márgenes, el contenido se recortaría. La ventana principal se crea con 1200 px de ancho y no se encontró un tamaño mínimo explícito (`setMinimumSize`), por lo que solo afectaría a quien la estreche mucho.
- No se pudieron ejecutar en el entorno de validación (Qt sin pantalla) `frontend_layout_responsiveness_auditor` ni `frontend_qt_window_lifecycle_auditor`, que terminan con *segmentation fault*; conviene correrlos en la máquina de desarrollo.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `test_view_prewarmer.py` | 6 pasan (orden y retardos, omisión de vistas ya abiertas, aplazamiento mientras se navega, parada al cerrar, aislamiento de fallos, idempotencia de `start`) |
| Batería relevante (frontend, contratos, handlers, controladores, auditores) | 97 pasan |
| Auditores CLI (fronteras, DRY, código muerto, ubicación, parámetros sin uso, tokens de diseño, textos, señales Qt) | Sin hallazgos |

**Fallos y limitaciones preexistentes, sin relación con este paso:**

- `test_giphy_and_tts_filter.py` (3 pruebas): dependen de la API key y de red de Giphy.
- `test_worker_and_core_lifecycle.py::test_chat_and_reward_workers_stop_sets_interruption_and_quit`: intermitente (carrera entre `run()` y `stop()` con `channel_name=""`).
- La suite completa y las pruebas que instancian la ventana principal producen *segmentation fault* en el entorno de validación. Las integraciones en `main_window.py` (cableado del planificador y desglose) no tienen prueba automatizada por esa razón; conviene correr la suite completa en la máquina de desarrollo y revisar el siguiente log.

## Pendiente (no incluido en este paso)

- **Aplicar `0007-perf-token-decrypt-cache.patch`** y comprobar en el siguiente log, con el nuevo desglose `[Perf/Integrations]`, si `auth` explica los ~300 ms de Settings. Si no los explica, los sospechosos restantes están en `dashboard`, `settings_view` (4 `unpolish`/`polish`) o `views` (reparto a ~7 vistas).
- **Triggers**: `_fetch_api_rewards()` se ejecuta en cada visita (≈ 27 ms de `hooks`).
- **Settings, creación**: ~410–450 ms; conviene medir qué parte corresponde a la enumeración de dispositivos de audio.
- **Arranque y cierre**: trabajo previo al splash e importación de `frontend.main_window`, y detención de workers (~1.1 s) que no se solapa por completo.
