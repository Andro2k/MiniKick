# Walkthrough WT-1.5.9_33: Soporte Multiplataforma de Recompensas con Mismo Nombre sin Sobreescrituras

## Novedades
- **Aislamiento Multiplataforma de Recompensas Homónimas**:
  - Ahora es posible crear y duplicar recompensas de puntos del canal que compartan exactamente el mismo nombre o título en diferentes plataformas (ej. tener una recompensa llamada "ctm" en Kick y otra llamada "ctm" en Twitch de forma simultánea e independiente).
  - La clave en memoria y persistencia se gestiona de forma unívoca bajo el formato estándar `f"{platform}:{reward_name}"`, garantizando que ninguna acción (creación, edición, duplicado o borrado) sobre una plataforma altere la configuración de otra.
- **Resolución Directa por Plataforma en `RewardsService`**:
  - Incorporado el método `get_reward_config(reward_name: str, platform: str = "kick") -> dict | None` para consultar la configuración activa de una recompensa asociada a una plataforma específica de forma instantánea.

## Mejoras
- **Esquema de Base de Datos Relacional (`obs_rewards` y `reward_redemptions`)**:
  - Se actualizó la definición formal de la tabla `obs_rewards` estableciendo la clave primaria compuesta `PRIMARY KEY (reward_name, platform)` en lugar de restringir únicamente `reward_name`.
  - Se desacopló la tabla histórica `reward_redemptions` eliminando la restricción obsoleta de clave foránea simple `FOREIGN KEY(reward_name) REFERENCES obs_rewards(reward_name)`.
  - Se implementó una migración automática no destructiva en `DatabaseManager._upgrade_schema()` que detecta tablas existentes y elimina el foreign key obsoleto, preservando el historial completo de redenciones y evitando errores de `foreign key mismatch`.
- **Eficiencia Big-O**:
  - **Búsqueda $\mathcal{O}(1)$ en Canjes en Vivo**: En `MainWindowCore._handle_reward_redeemed`, la resolución de la recompensa para el overlay y logs se realiza en tiempo constante $\mathcal{O}(1)$ mediante `self.rewards_service.get_reward_config(reward_name, platform=platform)`.
  - **Carga y Guardado $\mathcal{O}(n)$ de Pasada Única**: `SQLiteRewardsStorage.load_all()` y `save_all()` procesan todas las recompensas en una única iteración lineal $\mathcal{O}(n)$.
- **Experiencia de Usuario en `RewardsView`**:
  - La celda 0 de la tabla continúa mostrando el nombre limpio ("ctm"), mientras que la celda 1 visualiza la plataforma ("Kick" o "Twitch") con su respectivo distintivo y color.
  - Los botones de acción (`play`, `edit`, `duplicate`, `delete`) despachan internamente la clave unívoca de la fila para evitar ambigüedades.

## Correcciones
- **Corrección de `foreign key mismatch` en SQLite**:
  - Resuelto el error crítico `foreign key mismatch - "reward_redemptions" referencing "obs_rewards"` que impedía que cualquier operación de guardado o borrado se persistiera en la base de datos de SQLite, provocando que los cambios se revirtieran al recargar.
- **Eliminación de la Sobreescritura al Duplicar**:
  - Corregido el error por el cual duplicar una recompensa de Kick a Twitch manteniendo o asignando el mismo nombre sobreescribía la entrada en `mappings` y la eliminaba de la plataforma previa.
- **Independencia en Eliminación de Recompensas**:
  - Corregido el comportamiento donde eliminar una recompensa podía afectar a la homónima en otra plataforma. Ahora cada eliminación es estrictamente específica a su plataforma.
- **Disponibilidad de Nombres entre Plataformas**:
  - Corregido el cálculo en `RewardsController._get_available_rewards()` que bloqueaba nombres ya usados en una plataforma impidiendo seleccionarlos para la otra.
- **Prevención de Falsa Detección como 'Desvinculada'**:
  - Corregido el fallo por el cual recompensas duplicadas entre Twitch y Kick que compartían el mismo nombre se mostraban en la tabla como `Twitch (desvinculada)`. Al actualizar el mapa de recompensas remotas (`self.rewards_details_map`), ahora se almacenan claves compuestas (`f"{plat}:{title}"`) e índices por ID (`f"id:{details['id']}"`), impidiendo que los resultados de una plataforma sobreescriban a los de la otra.
  - La verificación remota en `RewardsView._render_rows` ahora comprueba de forma prioritaria la clave compuesta de plataforma y el identificador remoto de la recompensa en `self.remote_rewards_map`, evitando falsos positivos de desvinculación.
  - Sincronización en `RewardsConfigWizard` (`_filter_rewards_by_platform`, `_on_combo_reward_changed`, `get_config_data`) para discriminar los detalles y el identificador remoto (`reward_id`) según la plataforma activa sin contaminar selecciones entre Twitch y Kick.
