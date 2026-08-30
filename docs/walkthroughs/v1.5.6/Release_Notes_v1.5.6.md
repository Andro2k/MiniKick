# Release Notes - MiniKick Version 1.5.6

**28 de Agosto, 2026**

## Puntos de Canal Multi-Plataforma (Twitch + Kick) y Detección Proactiva de Archivos Faltantes

> [!NOTE]
> MiniKick v1.5.6 introduce el soporte integral de Puntos de Canal para **Twitch** (EventSub WebSocket + Helix API) junto a **Kick**, permitiendo crear, editar, vincular y activar alertas multimedia interactivas en OBS Studio desde ambas plataformas en tiempo real, además de incorporar detección y alertas de archivos multimedia faltantes.

---

### Novedades (2)

- **[FEATURE] [REWARDS] Soporte Multi-Plataforma de Puntos de Canal (Twitch + Kick):** Integración completa de puntos de canal de Twitch mediante EventSub WebSocket (`wss://eventsub.wss.twitch.tv/ws`) y la API Helix. Permite vincular recompensas existentes o crear nuevas tanto en Kick como en Twitch desde el asistente `RewardsConfigWizard`, visualizándolas en `RewardsView` con insignias temáticas e iconos nativos (`WT-1.5.6_01`).
- **[FEATURE] [REWARDS] Detección y Marcado Visual de Archivos Multimedia Faltantes:** Identificación en tiempo real de archivos inexistentes o movidos en la tabla de recompensas vinculadas, con iconos de alerta (`alert-triangle.svg`), texto en color rojo (`COLOR_RED`), tooltips descriptivos, indicador de advertencia en el encabezado de la tarjeta y notificaciones Toast explicativas al streamer tanto en previsualizaciones manuales como en canjes de espectadores en vivo (`WT-1.5.6_01`).

---

### Mejoras (8)

- **[IMPROVEMENT] [LOGGING] Estandarización de Logs de Desvinculación Multi-Plataforma:** Estandarización de los logs de auditoría de usuario (`[User Action] Requested unlinking/disconnecting <Platform>`, `[User Action] <Platform> unlinked/disconnected successfully`) en Kick, Twitch, YouTube y TikTok (`WT-1.5.6_05`).
- **[IMPROVEMENT] [TESTS] Reestructuración Modular por Capas y Fixtures Centralizados:** Reorganización completa de los 142 tests unitarios en subpaquetes modulares por capas arquitectónicas (`core/`, `database/`, `services/`, `providers/`, `ui/`), centralización de fixtures de alto rendimiento en memoria (`:memory:`) en `conftest.py` y ampliación de `run_tests.py` con banderas de ejecución granular (`--core`, `--db`, `--services`, `--providers`, `--ui`) y menú interactivo enriquecido (`WT-1.5.6_04`).
- **[IMPROVEMENT] [LOGGING] Estandarización Modular de Loggers Nombrados:** Migración integral del 100% de las llamadas directas al logger raíz `logging.<level>` hacia loggers nombrados a nivel de módulo (`logger = logging.getLogger("minikick.<module>")`) en todos los servicios, providers, workers, vistas y punto de arranque, garantizando consistencia, trazabilidad de logs y rendimiento $\mathcal{O}(1)$ (`WT-1.5.6_03`).
- **[IMPROVEMENT] [REPORTS] Botón Único de Envío y Autorelleno de Contacto Multi-Plataforma:** Optimización del diálogo de fallos críticos [`CrashReportDialog`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/crash_report_dialog.py) eliminando el botón secundario para dejar únicamente la acción directa de envío, e integración del método [`DatabaseManager.get_primary_identity`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/database/manager.py) para pre-llenar automáticamente en tiempo $\mathcal{O}(1)$ el nombre del usuario/canal activo o configurado (**Kick** $\to$ **Twitch** $\to$ **TikTok** $\to$ **YouTube**) en todos los reportes de error y feedback (`WT-1.5.6_02`).
- **[IMPROVEMENT] [REWARDS] Asistente de Recompensas con Selección de Plataforma:** `RewardsConfigWizard` permite elegir entre Kick y Twitch, filtrando dinámicamente las recompensas disponibles, auto-asignando el color temático característico (`#00e701` Kick, `#9146FF` Twitch) y gestionando la creación en sus respectivas APIs (`WT-1.5.6_01`).
- **[IMPROVEMENT] [REWARDS] Validación Temprana en Capa de Negocio:** Incorporación de `RewardsService.is_file_valid` para comprobar en tiempo constante $\mathcal{O}(1)$ la existencia física del archivo antes de enviar órdenes de renderizado al servidor overlay (`WT-1.5.6_01`).
- **[IMPROVEMENT] [DB] Migración Automática de Base de Datos:** `DatabaseManager` y `SQLiteRewardsStorage` añaden la columna `platform` a la tabla `obs_rewards` con migración automática y retrocompatibilidad total (`WT-1.5.6_01`).
- **[IMPROVEMENT] [I18N] Cobertura 100% de Traducciones:** Todas las nuevas cadenas de selección de plataforma, creación en API, tooltips y avisos incorporadas en `locales/es.json` y `locales/en.json` con paridad total (`WT-1.5.6_01`).

---

### Correcciones (4)

- **[FIX] [DASHBOARD] Desacoplamiento de Switch de Autostart:** Corregido el comportamiento del conmutador de autostart en `DashboardView`, el cual disparaba erróneamente la ventana OAuth de Kick al activarse en lugar de únicamente persistir la preferencia de arranque (`WT-1.5.6_05`).
- **[FIX] [SIDEBAR] Sincronización Dinámica del Perfil con Twitch y Fallbacks:** Corregida la falta de actualización del nombre de usuario y estado "Online" en la barra lateral al iniciar sesión con Twitch o desvincular cuentas (`WT-1.5.6_05`).
- **[FIX] [OVERLAYS] Eliminación de Fallos Silenciosos en OBS:** Corrección de eventos de canje y previsualizaciones que fallaban silenciosamente con errores HTTP 404 en el overlay sin notificar la causa (`WT-1.5.6_01`).
- **[FIX] [TESTS] Sincronización y Robustez de Test Runner:** Sincronización de suite en `resources/tests/run_tests.py` con manejo elegante de interrupciones `Ctrl+C` y suite dedicada `test_twitch_rewards.py` (`WT-1.5.6_01`).


---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.6 preserva íntegramente la base de datos previa, migrando automáticamente la tabla `obs_rewards` para soportar `platform` sin pérdida de datos.

