# Walkthrough WT-1.6.0_34: Rediseño Moderno de Piper TTS Dialog y Expansión de Voces de la Comunidad

## Novedades

1. **Nuevo Catálogo de Voces de la Comunidad y Efectos de Stream**:
   - Se expandió el catálogo en [`backend/services/chat/piper_manager.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/chat/piper_manager.py) con nuevos modelos en español populares de Hugging Face (`AIHeaven`, `csukuangfj`, `friyin`):
     - **GLaDOS (`es_ES-glados-medium`)**: Voz robótica icónica para alertas y donaciones de stream.
     - **Miro (`es_ES-miro-high`)**: Voz clara y expresiva de alta calidad.
     - **Alicia (`es_MX-alicia-medium`)**: Voz suave y natural optimizada.
     - **Mario (`es_MX-mario-medium`)**: Voz masculina natural y dinámica.
     - **Windows XP TTS (`es-xp-medium`)**: Síntesis retro con timbre clásico.
     - **Santa Claus (`es_MX-santaclosrmc-medium`)**: Voz grave festiva con carácter temático.
   - Soporte para descompresión y streaming de paquetes `.tar.gz` (`archive_url`) en `PiperVoiceManager.download_voice_sync`, extrayendo y normalizando los archivos `.onnx` y `.onnx.json`.

2. **Buscador y Filtrado en Tiempo Real**:
   - Barra de búsqueda reactiva integrada en [`frontend/dialogs/piper_dialog.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/dialogs/piper_dialog.py) que filtra instantáneamente por nombre del locutor, ID de modelo y código de región.
   - Pestañas segmentadas para clasificación inmediata (`Todas`, `Naturales`, `Personajes & Retro`, `Instaladas`), con escapado de ampersands para evitar guiones mnemónicos involuntarios.

3. **Panel de Síntesis Acústica Superior (`ExpandableCard`)**:
   - Los controles acústicos (Velocidad `length_scale`, Variabilidad de tono `noise_scale`, Cadencia `noise_w`) ahora se ubican en la sección superior como tarjeta colapsable, permitiendo ajustar parámetros sin empujar el footer ni desplazar el foco de navegación del catálogo inferior.
   - **Acciones Centralizadas**: El botón de **Importar Modelo ONNX** se integró dentro del card de ajustes en una barra de acciones junto al botón de **Restablecer Valores**, despejando por completo el encabezado del diálogo para una estética mucho más limpia y minimalista.

---

## Mejoras

1. **Unificación Visual bajo Tarjeta Maestra (`ModernCard`)**:
   - Se eliminaron los bordes individuales por cada ítem que generaban fatiga visual y márgenes dobles.
   - La lista de voces ahora reside dentro de un contenedor único `ModernCard` con separadores edge-to-edge `ModernDivider` entre filas, manteniendo el estándar de diseño Antigravity.
   - Gestión inteligente del último divisor visible: al filtrar por búsqueda o categoría, el último elemento visible oculta su divisor inferior para evitar líneas residuales sobre el borde del card.

2. **Botón de Eliminación Compacto (Solo Icono Papelera)**:
   - En [`frontend/components/dialogs/piper_voice_item.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/dialogs/piper_voice_item.py), el botón de eliminación se optimizó a un botón cuadrado simétrico de `30x30` con icono de papelera roja (`trash-filled.svg`) y tooltip de confirmación, alineándose con el botón de prueba de audio.
   - Para la voz por defecto del sistema (`Claude`), el botón de eliminación se oculta por completo en lugar de mostrarse deshabilitado, eliminando la sensación visual de botón bugeado.

3. **Eliminación de `setStyleSheet` Sueltos**:
   - Se retiraron las llamadas inline `setStyleSheet("background: transparent;")` en el área de scroll y su widget de contenido dentro de `piper_dialog.py`, apoyándose en las reglas nativas del motor de estilos centralizado de [`frontend/common/theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/common/theme.py) (`GLOBAL_QSS`).

4. **Estandarización Absoluta de i18n**:
   - Todas las etiquetas de UI, placeholders de búsqueda, títulos de pestañas, tooltips y contadores fueron incorporados a los archivos de localización:
     - [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json)
     - [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json)
     - [`backend/config/locale_defaults.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/config/locale_defaults.py)
   - Cero cadenas de texto hardcodeadas ni fallbacks inline con operadores lógicos.

5. **Auditoría AST y Cobertura de Pruebas**:
   - Limpieza de importaciones innecesarias (`dead_code_manager.py` reporta 0 imports huérfanos).
   - Verificación de parámetros (`unused_parameter_manager.py` reporta 0 parámetros no utilizados).
   - Pruebas unitarias en [`resources/tests/test_antigravity_ui_theme.py`](file:///c:/Users/TheAn/Desktop/python/Kick/resources/tests/test_antigravity_ui_theme.py) (`test_piper_voices_dialog_modern_structure_and_catalog`), logrando 52/52 pruebas pasadas.

---

## Correcciones

1. **Corrección de Voces Importadas que Mostraban Opción de Descarga al Eliminarse**:
   - Se corrigió el flujo de eliminación en `_delete_voice`: cuando se elimina una voz local importada (que carece de URL de descarga web), el diálogo refresca el catálogo y remueve el ítem por completo de la interfaz, impidiendo que aparezca como modelo disponible para descargar.
   - En `PiperVoiceItemWidget`, el botón de descarga se inhibe estrictamente para modelos marcados como personalizados (`is_custom`).
2. **Corrección de Botón de Eliminación en Voz Predeterminada**:
   - Para la voz inicial del sistema (`es_MX-claude-high`), se suprimió el botón de eliminación en lugar de mantener un botón gris inactivo, resolviendo el defecto visual reportado.
3. **Gestión de Separadores Residuales en Filtrado**:
   - Se corrigió el comportamiento donde listas filtradas dejaban divisores huérfanos o dobles márgenes al ocultar elementos intermedios.
