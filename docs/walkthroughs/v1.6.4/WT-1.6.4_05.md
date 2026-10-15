# Walkthrough Técnico - v1.6.4 / WT-1.6.4_05

**Versión**: v1.6.4  
**Fecha**: 2026-10-15  
**Origen**: Retorno automático del chat al minimizar su ventana flotante.

---

## Novedades

Al minimizar la ventana independiente del chat, el panel vuelve automáticamente a la vista principal del
módulo Chat.

## Mejoras

El retorno automático y el cierre de la ventana comparten una operación protegida contra llamadas duplicadas.
El panel conserva su posición y proporción originales al regresar.

## Correcciones

Se evita que el chat quede alojado en una ventana minimizada y sin dimensiones visibles. El cambio se detecta
al recibir la transición de estado de ventana a minimizada.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `frontend/views/chat_view.py` | Retorno automático del panel al minimizar la ventana flotante |

---

## Verificación

- No se ejecutaron pruebas automatizadas.
