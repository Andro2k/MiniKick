# Walkthrough Técnico — MiniKick v1.6.7 (Paso 07)

La ventana flotante del chat conserva la posición y el tamaño usados en el desacoplamiento anterior cuando el usuario vuelve a acoplar y desacoplar el panel. El estado se mantiene durante la vida de la vista actual de Chat.

---

## Novedades

- Al desacoplar el chat por primera vez se mantiene el tamaño inicial de la ventana.
- En desacoplamientos posteriores, se restaura la geometría del último desacoplamiento.

## Mejoras

- `ChatView` conserva la geometría Qt al devolver el panel a la vista principal y la aplica a la siguiente ventana flotante.
- La geometría restaurada respeta la posición, el tamaño y el estado que Qt guarda en `saveGeometry`.

## Correcciones

- La ventana del chat ya no vuelve a su posición inicial cada vez que se desacopla después de haber sido reanclada.
- El cierre de la ventana flotante y el botón de reanclaje siguen usando el flujo existente para devolver el panel.

> [!NOTE]
> La geometría se conserva durante la vida de la vista Chat, pero no se persiste entre reinicios de MiniKick.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `$env:QT_QPA_PLATFORM='offscreen'; .\.venv\Scripts\python.exe -m pytest resources\tests\test_chat_detached_window.py --tb=short -q` | 9 aprobadas |
| `.\.venv\Scripts\python.exe resources\tools\project_quality_suite.py --quick` | 11/12 aprobadas; falla únicamente Project Translation Keys por `music.youtube.com` en `backend/utils/youtube_url.py`, falso positivo conocido y ajeno a este cambio |
| `git diff --check` | Sin errores de whitespace |
