# Walkthrough Técnico — MiniKick v1.6.8 (Paso 02)

El bloque del overlay de música pasa a una tarjeta expandible y su vista previa usa una sola paleta (neutros del tema y verde de acento).

---

## Novedades

- La tarjeta del overlay (URL, diseño, vista previa y botón de copiar) es ahora un `ExpandableCard` sin interruptor, colapsada por defecto, para que la pestaña **Reproductor** quede más corta.

## Mejoras

- **Paleta única en la vista previa:** `music_mockup.py` usa `Palette.NEUTRAL_*` para fondo, borde y textos y `BrandColors.GREEN` / `GREEN_800` para el acento, la portada y la etiqueta del vinilo. Ya no aparecen crema, rosa, morado ni verde oliva.
- **Menos constantes:** se eliminaron de `MockupPalette` las ocho constantes `MUSIC_VINYL_*` y `MUSIC_CARD_*`. `MUSIC_ART_ACCENT` se conserva porque `AVATAR_GRADIENTS` (mockup del chat) la usa.
- `_draw_album_art_placeholder` pierde el parámetro `with_third_stop`, que solo servía para el tercer color.

## Notas

- Solo cambia la vista previa dentro de la app. El overlay real que se muestra en OBS (`assets/overlays/music/music.html`) no se tocó.
