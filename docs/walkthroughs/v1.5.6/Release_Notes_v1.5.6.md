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

### Mejoras (4)

- **[IMPROVEMENT] [REWARDS] Asistente de Recompensas con Selección de Plataforma:** `RewardsConfigWizard` permite elegir entre Kick y Twitch, filtrando dinámicamente las recompensas disponibles, auto-asignando el color temático característico (`#00e701` Kick, `#9146FF` Twitch) y gestionando la creación en sus respectivas APIs (`WT-1.5.6_01`).
- **[IMPROVEMENT] [REWARDS] Validación Temprana en Capa de Negocio:** Incorporación de `RewardsService.is_file_valid` para comprobar en tiempo constante $\mathcal{O}(1)$ la existencia física del archivo antes de enviar órdenes de renderizado al servidor overlay (`WT-1.5.6_01`).
- **[IMPROVEMENT] [DB] Migración Automática de Base de Datos:** `DatabaseManager` y `SQLiteRewardsStorage` añaden la columna `platform` a la tabla `obs_rewards` con migración automática y retrocompatibilidad total (`WT-1.5.6_01`).
- **[IMPROVEMENT] [I18N] Cobertura 100% de Traducciones:** Todas las nuevas cadenas de selección de plataforma, creación en API, tooltips y avisos incorporadas en `locales/es.json` y `locales/en.json` con paridad total (`WT-1.5.6_01`).

---

### Correcciones (2)

- **[FIX] [OVERLAYS] Eliminación de Fallos Silenciosos en OBS:** Corrección de eventos de canje y previsualizaciones que fallaban silenciosamente con errores HTTP 404 en el overlay sin notificar la causa (`WT-1.5.6_01`).
- **[FIX] [TESTS] Sincronización y Robustez de Test Runner:** Sincronización de suite en `resources/tests/run_tests.py` con manejo elegante de interrupciones `Ctrl+C` y suite dedicada `test_twitch_rewards.py` (`WT-1.5.6_01`).

---

> [!IMPORTANT]
> **Notas de Actualización:**
> La versión 1.5.6 preserva íntegramente la base de datos previa, migrando automáticamente la tabla `obs_rewards` para soportar `platform` sin pérdida de datos.
