# Walkthrough Técnico - v1.6.4 / WT-1.6.4_03

**Versión**: v1.6.4  
**Fecha**: 2026-10-15  
**Origen**: Ajustes de tamaño y restauración del chat desacoplado.

---

## Novedades

No se agregan funciones nuevas. Se ajusta el comportamiento de la ventana flotante de chat.

## Mejoras

### Ventana flotante redimensionable

El chat desacoplado ahora se presenta como una ventana normal redimensionable, con un tamaño mínimo que
mantiene utilizables el historial y sus controles.

### Restauración del espacio original

Al desacoplar el panel se guarda su posición y proporción dentro del layout. Al devolverlo, se inserta en el
mismo lugar con el mismo factor de expansión, evitando que el historial quede más ancho y altere el espacio de
los demás controles.

## Correcciones

Se corrigió la proporción del layout al volver a acoplar el chat: antes el panel se agregaba al final con un
factor de expansión fijo, que podía ampliar el área del chat y reducir la de los otros controles.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `frontend/views/chat_view.py` | Ventana redimensionable y restauración de posición y factor de expansión originales |

---

## Verificación

- No se ejecutaron pruebas automatizadas.
