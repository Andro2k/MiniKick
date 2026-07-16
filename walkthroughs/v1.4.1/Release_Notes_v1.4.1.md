# Release Notes | MiniKick v1.4.1
*Mejoras en Moderación y Anti-Spam, Lista Negra de Palabras para TTS, Filtrado por Fecha en Logs, Validación de Diálogos y Reestructuración de la Interfaz Gráfica*

En esta versión (v1.4.1), MiniKick se consolida como una herramienta más madura, limpia y robusta. Hemos optimizado la arquitectura de la interfaz reduciendo dependencias acopladas, implementado un completo sistema de lista negra de palabras prohibidas para la síntesis de voz (TTS), y expandido las capacidades de moderación anti-spam con soporte de expulsiones permanentes (Bans) mediante la API de Kick y listas blancas de dominios seguros. Además, corregimos importantes bugs de usabilidad (como la persistencia de la barra de búsqueda y el resaltado de texto en los spinboxes) e introdujimos un filtro de logs por fecha para facilitar diagnósticos precisos.

---

## 1. Reestructuración de la Interfaz y Limpieza de Código (DRY)
Simplificamos la estructura interna del código del frontend para reducir el acoplamiento y facilitar el mantenimiento de la interfaz gráfica:
* **Fusión de Componentes Huérfanos**: Fusionamos componentes que solo tenían un consumidor con sus respectivas vistas y diálogos padres (ej. fusionamos `DraggableBox` en `VisualPositionerDialog`, `LogControlsPanel` en `LogView` y `ExpandableSettingCard` en `blocks.py`), eliminando archivos innecesarios.
* **Componentes Genéricos Centralizados**: Centralizamos los layouts reutilizables en `frontend/widgets/` dándoles nombres limpios e identificables (`blocks.py`, `controls.py`, `table.py`).
* **Simplificación de la Carpeta de Chat**: Movimos los subcomponentes de chat de una carpeta anidada a la carpeta raíz de chat, renombrándolos para reflejar de forma exacta su propósito (`bot_mute.py`, `chat_display.py`, `tts_settings.py`, `overlay_settings.py`).

---

## 2. Lista Negra de Palabras Prohibidas para TTS (Blacklist)
Implementamos una lista negra de palabras prohibidas para el bot de Text-to-Speech (TTS):
* **Filtro Sensible a Límites**: El motor realiza búsquedas de expresiones regulares `\b<palabra>\b` sobre el mensaje de chat antes de enviarlo a reproducir. Las sub-palabras no se ven afectadas (ej. `clase` no activa la palabra `ase`), evitando falsos positivos.
* **Interfaz de Administración**: Agregamos una sección exclusiva de "Palabras Prohibidas" en la pestaña de usuarios silenciados con una barra de inserción rápida y una lista de etiquetas dinámicas con botones individuales de eliminación.
* **Persistencia en SQLite**: La lista se guarda de manera persistente en la clave `tts_banned_words` de los ajustes globales.

> [!IMPORTANT]
> El filtro de palabras prohibidas distingue entre límites de palabras completos, lo que significa que palabras ofensivas o no deseadas se bloquearán sin entorpecer la conversación normal de términos legítimos que contengan sub-palabras similares.

---

## 3. Mejoras Anti-Spam: Lista Blanca de Enlaces y Penalizaciones
Robustecimos el módulo de protección contra spam para dar mayor control al streamer ante ataques o enlaces no autorizados:
* **Lista Blanca de Dominios (Allowlist)**: Agregamos soporte para definir dominios permitidos separados por comas (ej. `clips.kick.com, youtube.com`) bajo el filtro de **Protección de Enlaces**. Los enlaces correspondientes a estos dominios se ignoran de las sanciones de spam.
* **Nuevas Acciones de Moderación**:
  * **Expulsar (Ban)**: Permite banear permanentemente a un usuario infractor utilizando la API oficial de Kick (`POST /public/v1/moderation/bans`).
  * **Advertir y Borrar**: Elimina el mensaje y envía una advertencia pública en el chat dirigiéndose directamente al usuario infractor (`@usuario por favor evita el spam en el chat.`).

> [!TIP]
> Puedes ingresar tantos dominios permitidos en la lista blanca como desees separados por comas. El filtro buscará sub-coincidencias, de modo que registrar `kick.com` permitirá tanto `clips.kick.com` como `kick.com/streamer`.

---

## 4. Configuración de Duración en Minutos y Migración SQL
* **Ajuste en Minutos**: Modificamos el selector de duración de penalizaciones de spam para configurarse en minutos en lugar de segundos, alineándolo con las especificaciones de Kick (rango de 1 a 10080 minutos).
* **Migración Silenciosa**: Implementamos una migración en SQL en `manager.py` que divide de forma automática entre 60 cualquier configuración antigua de segundos (ej. `300` o `600`) convirtiéndola a minutos al iniciar la aplicación sin pérdida de datos.

> [!NOTE]
> La migración de base de datos se ejecuta de manera interna e invisible la primera vez que inicia la versión v1.4.1. No requiere de ninguna intervención manual o mantenimiento.

---

## 5. Filtrado por Fecha en el Visor de Logs del Sistema
* **Filtro Avanzado**: Añadimos una casilla de verificación y un selector `QDateEdit` con calendario en el visor de logs.
* **Actualización en Tiempo Real**: El filtro aplica restricciones por fecha (`YYYY-MM-DD`) directamente en la base de datos (con cláusulas `LIKE ?`) para consultas históricas y de forma reactiva sobre los logs entrantes por streaming.

---

## 6. Corrección de Bugs de Usabilidad y Pulido Visual
* **Rediseño de SpinBoxes**: Los botones de incrementar/decrementar de `QSpinBox` y `QDoubleSpinBox` ahora se posicionan adyacentes horizontalmente. Desactivamos el bloque de selección azul/verde del texto interno para que las interacciones con flechas sean limpias.
* **Persistencia del Buscador**: Corregimos el bug de tablas que ocultaba la barra de búsqueda al filtrar términos que devolvían cero coincidencias. La barra ahora permanece visible durante búsquedas activas.
* **Validación de Wizard**: El botón "Siguiente" en el asistente de creación de temporizadores se deshabilita si el campo del nombre o la lista de mensajes de respuesta están vacíos.
* **Estilo Integrado para QDateEdit**: Creamos estilos oscuros y chevrons coherentes para el selector de fechas integrándolo con la paleta de colores premium de MiniKick.
