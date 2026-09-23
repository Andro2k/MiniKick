# Walkthrough v1.6.0_40 - Nuevos Auditores de Calidad de Código y Detección de Antipatrones

## Novedades

1. **Anti-Hardcode & i18n Leak Auditor (`resources/tools/anti_hardcode_auditor.py`)**:
   - Herramienta de análisis estático basada en AST (`AntiHardcodeVisitor`) para auditar la regla de oro: Cero textos visibles hardcodeados en la interfaz de usuario.
   - Detecta literales de cadenas directas pasadas a constructores de widgets Qt (`QLabel`, `QPushButton`, `ModernButton`, `QCheckBox`, etc.).
   - Detecta llamadas a setters de texto (`setText`, `setPlaceholderText`, `setToolTip`, `setWindowTitle`, `show_toast`) que omiten `self.i18n.get(...)`.
   - Detecta antipatrones de fallback inline ilegales (`self.i18n.get("key") or "Fallback"`).
   - Ignora de forma segura cadenas técnicas, enums de Qt, nombres de iconos, roles QSS y expresiones regulares.
   - Soporte para CLI `--check`, `--json` y `--strict`.

2. **Qt Signal & Event Loop Leak Auditor (`resources/tools/qt_signal_leak_auditor.py`)**:
   - Herramienta AST (`SignalLeakVisitor`) para prevenir fugas de memoria y multiplicaciones de listeners de eventos en PyQt6.
   - Detecta llamadas `.connect(...)` dentro de bucles `for` o `while` sobre widgets no transitorios (`LOOP_CONNECT`).
   - Detecta llamadas `.connect(...)` dentro de métodos de refresco periódico o repintado recurrente como `render_*`, `populate_*`, `paintEvent` o `update_*` (`REFRESH_METHOD_CONNECT`).
   - Detecta closures lambda con captura tardía (*late-binding closure*) en bucles sin default arg binding (`item=item`).
   - Permite de forma segura inicializaciones estáticas en métodos de setup (`_connect_signals`, `__init__`).

3. **DRY Duplication & AST Clone Auditor (`resources/tools/dry_duplication_auditor.py`)**:
   - Auditor de similitud estructural AST (`DuplicationScanner`, `ASTNormalizer`) que anonimiza nombres de variables y literales en $\mathcal{O}(N)$ para comparar huellas SHA-256 de subárboles sintácticos en $\mathcal{O}(1)$.
   - Agrupa clusters de código duplicado con longitud $\ge 5$ u $\ge 8$ sentencias consecutivas.
   - Muestra snippets con líneas exactas, archivos implicados y funciones para orientar refactorizaciones.

4. **Design Token & Style Auditor (`resources/tools/design_token_auditor.py`)**:
   - Auditor estático para velar por la coherencia visual con el sistema Figma / Antigravity.
   - Detecta valores hexadecimales `#RRGGBB` hardcodeados en widgets fuera de `theme.py`.
   - Ofrece sugerencias automáticas de tokens de color existentes (`COLOR_TWITCH`, `COLOR_KICK`, `COLOR_GREEN`, `COLOR_PURE_WHITE`, etc.).
   - Detecta estilos inline `setStyleSheet(...)` no autorizados fuera de los componentes base.

5. **Suite de Pruebas Automatizadas (`resources/tests/test_quality_auditors.py`)**:
   - 6 nuevos tests unitarios que validan la precisión y ausencia de falsos positivos en los 4 nuevos auditores estáticos.

---

## Mejoras

1. **Integración en la Suite Maestra (`resources/tools/system_health_audit.py`)**:
   - Ampliación de la suite integral de 7 a **11 herramientas de control de calidad**:
     - `Icon Toolkit & Integrity` (`icon_manager.py`)
     - `i18n Internationalization` (`i18n_manager.py`)
     - `Anti-Hardcode UI Auditor` (`anti_hardcode_auditor.py`)
     - `Dead Code & Orphan Scanner` (`dead_code_manager.py`)
     - `QSS Role & State Auditor` (`role_manager.py`)
     - `Unused Parameter Auditor` (`unused_parameter_manager.py`)
     - `Qt Signal Leak Auditor` (`qt_signal_leak_auditor.py`)
     - `Design Token Auditor` (`design_token_auditor.py`)
     - `DRY Duplication Auditor` (`dry_duplication_auditor.py`)
     - `Window & HWND Leak Auditor` (`window_audit_manager.py`)
     - `UI Flex & Responsive Matrix` (`ui_flex_inspector.py`)
   - Menú interactivo expandido con opciones directas del `1` al `13` y ejecución automatizada en modo CLI (`--all`, `--quick`, `--json`).
   - Métodos dedicados `check_anti_hardcode`, `check_signal_leaks`, `check_dry_duplication` y `check_design_tokens` con tiempos de respuesta en milisegundos.

2. **Rendimiento y Eficiencia Big-O**:
   - Todos los auditores nuevos ejecutan análisis sintáctico en una sola pasada de tokens/AST $\mathcal{O}(N)$ sin bloqueos ni dependencias de runtime Qt (excepto `ui_flex_inspector`).
   - El escaneo completo de 210 archivos y 11 herramientas finaliza en ~16.4 segundos.

---

## Correcciones

- No se registraron crashes en el código de producción. Se solventaron discrepancias de falsos positivos en el análisis estático de Qt para loops de inicialización de switches/controles (`_connect_signals`) y selectores de color (`color_picker.py`).
