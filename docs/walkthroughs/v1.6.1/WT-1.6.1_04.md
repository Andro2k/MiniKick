# Walkthrough WT-1.6.1_04 — Sistema de Bienvenida, Novedades de Versión y Badges 'N' Reactivos

## Resumen de la Versión
* **Versión:** `v1.6.1`
* **Tipo:** Nueva Característica UI/UX, Dominio de Novedades y Persistencia de Estado
* **Módulos Afectados:**
  * [`backend/services/system/whats_new_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py)
  * [`backend/services/system/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/__init__.py)
  * [`backend/services/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/__init__.py)
  * [`frontend/navigation/sidebar_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py)
  * [`frontend/dialogs/whats_new_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/whats_new_dialog.py)
  * [`frontend/dialogs/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/__init__.py)
  * [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py)
  * [`frontend/common/__init__.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/__init__.py)
  * [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py)
  * [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
  * [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
  * [`resources/tests/test_whats_new_system.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_whats_new_system.py)

---

## Novedades

### 1. Insignias 'N' Naranja Reactivas en la Barra Lateral (`Sidebar`)
* **Notificación de Módulos Actualizados:**
  En [`frontend/navigation/sidebar_component.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/navigation/sidebar_component.py), cada botón de navegación (`nav_button`) incorpora una insignia circular naranja/coral (`COLOR_ORANGE`) con la letra "N" en blanco, alertando al streamer de funciones nuevas o refactorizadas en esa sección.
* **Comportamiento en Estado Colapsado y Expandido:**
  * En modo expandido, la insignia de 18x18px se posiciona a la derecha del botón.
  * En modo colapsado (sidebar retraído a 60px), las insignias se adaptan a un tamaño compacto de 12x12px en la esquina superior del botón, y el botón de alternancia (`btn_toggle`) refleja la insignia "N" global si hay novedades pendientes de explorar.
* **Auto-Descarte al Visitar:**
  Al hacer clic en cualquier sección con insignia, esta se oculta inmediatamente y se emite la señal `section_viewed(view_name)`.

### 2. Modal de Bienvenida e Introducción a la Versión (`WhatsNewDialog`)
* **Diálogo Estético Dark-Mode:**
  En [`frontend/dialogs/whats_new_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/whats_new_dialog.py), se construyó una ventana modal basada en [`ModernModal`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/base_dialog.py) con tarjetas visuales (`whats_new_card`), iconos representativos e información clara para el streamer.
* **Modo Onboarding y Modo Actualización:**
  * Para nuevos usuarios (`is_first_launch`), se presenta como diálogo de bienvenida ("¡Bienvenido a MiniKick!") introduciendo la herramienta.
  * Para usuarios existentes tras una actualización, muestra las novedades clave de la versión (ej. Filtros Anti-Spam en Chat, Servidor de Overlays optimizado, Registro de conexiones estilo Jellyfin).

### 3. Servicio de Negocio Desacoplado (`WhatsNewService`)
* **Gestión de Versiones y Novedades:**
  En [`backend/services/system/whats_new_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/system/whats_new_service.py), se encapsuló la lógica de detección de versión (`last_seen_app_version`), catálogo estructurado de aspectos destacados (`_HIGHLIGHTS_CATALOG`) y persistencia de secciones exploradas (`seen_badges_vX.X.X`).

---

## Mejoras

### 1. Eficiencia Big-$\mathcal{O}$ y Rendimiento de Persistencia
* **Acceso y Almacenamiento en $\mathcal{O}(1)$:**
  La consulta de versión y de insignias vistas se realiza directamente en memoria y almacenamiento clave-valor SQLite mediante `set` nativo de Python, sin búsquedas lineales ni deserializaciones redundantes.
* **Cero Impacto en el Arranque:**
  La evaluación del diálogo se delega mediante `QTimer.singleShot(750, self._check_whats_new_dialog)` en [`backend/core/main_window_core.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/core/main_window_core.py), garantizando que la ventana principal renderice de inmediato sin bloqueos de interfaz.

### 2. Estandarización de Tokens y Roles QSS
* **Nuevos Tokens Centralizados en `theme.py`:**
  En [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py), se integraron los tokens de color (`COLOR_ORANGE`, `COLOR_ORANGE_DARK`, `COLOR_ORANGE_HOVER`, `COLOR_ORANGE_GLOW`) y los roles QSS `QLabel[role="badge_new"]` (con estado `collapsed`) y `QFrame[role="whats_new_card"]`.
* **Cero Estilos Inline:**
  Se evitó cualquier llamada directa a `setStyleSheet(...)`, manteniendo 100% de cumplimiento con [`design_token_auditor.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/design_token_auditor.py) y [`role_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/role_manager.py).

---

## Correcciones

### 1. Paridad de Internacionalización e Integridad de Iconos
* **Claves de Traducción Completas:**
  Se añadieron 13 nuevas claves en [locales/en.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json) y [locales/es.json](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) bajo el namespace `whats_new.*`, manteniendo paridad absoluta del 100% y cero textos visibles hardcodeados.
* **Sincronización con Catálogo de Iconos Físicos:**
  Se validaron las referencias de iconos SVG contra los 108 recursos físicos existentes en `assets/icons/`, resolviendo discrepancias y obteniendo pase limpio en [`icon_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tools/icon_manager.py).
