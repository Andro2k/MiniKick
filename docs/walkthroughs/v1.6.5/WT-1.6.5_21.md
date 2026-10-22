# Walkthrough Técnico - MiniKick v1.6.5 (Paso 21)

Se renovó la bienvenida del Dashboard con una tarjeta de configuración inicial, progreso basado en datos reales y accesos a las secciones existentes.

---

## Novedades

- La bienvenida presenta cuatro pasos: conectar una plataforma, crear un comando, configurar un timer y vincular una recompensa.
- Cada paso permite abrir su sección correspondiente o iniciar la conexión de Kick.
- Se agregaron traducciones para español e inglés y estilos QSS propios para los estados de progreso.

## Mejoras

- El porcentaje se calcula con el estado de conexión y las métricas existentes del Dashboard; no agrega consultas ni inventa valores de configuración.
- El panel acomoda su distribución en ventanas estrechas y actualiza los estados únicamente cuando cambian.
- La navegación desde las acciones de bienvenida también sincroniza la selección de la barra lateral.

## Correcciones

- Se retiró el estado vacío anterior de perfil que duplicaba la información de bienvenida.
- Se eliminaron las dos traducciones que quedaron sin uso tras retirar ese estado.

## Archivos Modificados

- `frontend/views/dashboard_view.py`
- `frontend/main_window.py`
- `frontend/common/theme.py`
- `locales/en.json`
- `locales/es.json`

## Verificación

- `python -m compileall -q frontend`: correcto.
- Validación de `locales/en.json` y `locales/es.json`: correcta.
- Suite rápida de calidad MiniKick: 12/12 controles aprobados.
- PySide6 no está disponible en este entorno; queda pendiente comprobar el renderizado visual real.
