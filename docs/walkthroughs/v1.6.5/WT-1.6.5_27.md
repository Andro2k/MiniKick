# Walkthrough Técnico — MiniKick v1.6.5 (Paso 27)

Se añadió una preferencia para que cada usuario elija si MiniKick descarga automáticamente las actualizaciones disponibles al iniciar. La instalación sigue requiriendo confirmación, de modo que la actualización no reinicia la aplicación sin autorización.

---

## Novedades

- Se incorporó en Ajustes un switch para activar o desactivar la descarga automática de actualizaciones.
- Cuando la opción está activa y la comprobación silenciosa encuentra una versión nueva, MiniKick inicia su descarga en segundo plano.
- Al finalizar la descarga, se solicita confirmación antes de instalar y reiniciar. Si se rechaza, el archivo descargado permanece disponible y la aplicación continúa abierta.

## Mejoras

- La preferencia se conserva entre sesiones y está desactivada por defecto, manteniendo el flujo de actualización manual para quienes no la habiliten.
- Se evita iniciar otra descarga automática si ya hay una descarga de actualización activa.
- Los textos de la opción, el progreso y la confirmación están disponibles en español e inglés.

## Correcciones

- Se valida que la actualización incluya una URL de descarga antes de iniciar el worker y se registra el motivo cuando no puede comenzar.
- Los errores de descarga se notifican al usuario, sin abrir el diálogo de instalación.

## Validación

- Las cinco pruebas específicas de la preferencia, el switch, la descarga condicional y la confirmación de instalación pasaron.
- La suite rápida de calidad aprobó las 12 auditorías del proyecto.
