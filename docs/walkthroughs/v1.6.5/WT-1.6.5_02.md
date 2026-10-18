# Walkthrough Técnico - v1.6.5 / WT-1.6.5_02

**Versión**: v1.6.5  
**Fecha**: 2026-10-16  
**Origen**: Ajustes responsivos para las fuentes de OBS de música.

---

## Novedades

No se agregan funciones nuevas.

## Mejoras

### Adaptación al tamaño disponible

Los modelos Classic y Vinyl ahora limitan su ancho y alto al espacio visible de la fuente. La portada, el disco, el brazo y el espaciado se escalan de acuerdo con el ancho y la altura disponibles, conservando los tamaños recomendados como referencia para OBS.

El modelo Classic ya no muestra la fila de controles decorativos debajo del progreso, dejando más espacio a la canción y a su portada.

### Texto largo en Vinyl

El título y el artista del modelo Vinyl mantienen el truncado con puntos cuando exceden el espacio disponible, igual que en Classic. Esto evita que texto extenso empuje o cubra el disco.

## Correcciones

Se corrigió el recorte del disco y del brazo de Vinyl al usar fuentes de OBS más pequeñas que el tamaño recomendado. También se evita que los metadatos largos desborden el área de texto.

---

## Verificación

- Se revisaron las reglas de tamaño para los dos modelos, incluidos los ajustes para fuentes bajas.
- Se ejecutó `git diff --check`.
- No se ejecutaron pruebas automatizadas.
