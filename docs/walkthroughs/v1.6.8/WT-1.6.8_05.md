# Walkthrough Técnico — MiniKick v1.6.8 (Paso 05)

La vista previa de video pasa a la pestaña Reproductor y se corrigen las esquinas de las pestañas, los sliders y el ruido del log.

---

## Novedades

- La vista previa de video vive en la pestaña **Reproductor** (debajo del overlay). Al pulsar ▶ en el historial, la vista cambia a esa pestaña y abre el video.

## Mejoras

- **Esquinas:** el panel de una pestaña tiene la esquina superior izquierda recta, pero las tarjetas de Cola e Historial la tenían redonda y dejaban una cuña visible. Esas tarjetas llevan ahora la propiedad `tab_flush="true"`: esquina superior izquierda recta y el resto con `RAD_LRG`, igual que el panel.
- **Sliders:** el handle salía como un rectángulo sin redondear porque `margin-top` y `margin-bottom` negativos por separado anulan el `border-radius`. Ahora se usa `margin: -5px 0` y las medidas salen de `Size.SLIDER_GROOVE` y `Size.SLIDER_HANDLE`. La barra queda en forma de píldora (radio = mitad del alto).
- **Log:** `bootstrap/environment.py` añade `js.warning=false` a `QT_LOGGING_RULES`. Los avisos `Unrecognized feature: 'web-share'` y `Failed to create WebGPU Context Provider` venían de la consola JS de la página de YouTube incrustada, no de la app.

## Limitaciones conocidas

- `QFont::setPointSize: Point size <= 0 (-1)` apareció una vez, en la sesión anterior a la vista previa, y no se pudo reproducir sin pantalla. Si vuelve a salir, anotar qué se estaba haciendo (hover, menú, desplegable).
- `[WhatsNew] GitHub release notes unavailable ... No highlights parsed` ya existía y no se tocó.
