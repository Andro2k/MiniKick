# Walkthrough Técnico - v1.6.4 / WT-1.6.4_01

**Versión**: v1.6.4  
**Fecha**: 2026-10-15  
**Origen**: Corrección de errores de Edge TTS y permisos OAuth para Twitch EventSub.

---

## Novedades

### Compatibilidad con el protocolo actual de Edge TTS

Se actualizó la versión mínima de `edge-tts` a `7.3.1` en los manifiestos de dependencias y se sincronizó
`uv.lock`. La versión anterior (`7.2.8`) utilizaba el handshake antiguo de Microsoft Edge Read Aloud y podía
fallar con `403 Invalid response status` al abrir el WebSocket de síntesis.

La solución actualiza la biblioteca; no cambia el comportamiento del proveedor ni elimina el fallback de
descarga durante la reproducción.

### Permisos OAuth para alertas de Twitch

Se añadieron los permisos requeridos para registrar las suscripciones EventSub de suscripciones y Cheers:

- `channel:read:subscriptions`: eventos `channel.subscribe`, `channel.subscription.message` y
  `channel.subscription.gift`.
- `bits:read`: evento `channel.cheer`.

El flujo OAuth de Twitch ahora solicita ambos scopes. También se incorporaron al control de permisos pendientes
y a los textos de interfaz en inglés y español. Para que tengan efecto, el usuario debe renovar los permisos de
Twitch desde MiniKick y aceptar los nuevos scopes; un token ya almacenado no los obtiene automáticamente.

---

## Correcciones

### Error 403 al crear suscripciones Twitch EventSub

La conexión WebSocket podía establecerse correctamente, pero Twitch rechazaba con HTTP 403 las solicitudes
para crear las cuatro suscripciones de suscripciones y Cheers. La causa era que el token OAuth no incluía los
scopes exigidos por Twitch. Al agregar los scopes al flujo de autorización, las suscripciones podrán crearse
después de que se renueven los permisos.

Los demás tipos EventSub se siguen intentando registrar de forma independiente; un error de autorización en
una suscripción no impide que el dispatcher continúe con las siguientes.

---

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `pyproject.toml` | Requisito mínimo de `edge-tts` actualizado a `>=7.3.1` |
| `requirements.in` | Requisito mínimo de `edge-tts` actualizado a `>=7.3.1` |
| `requirements.txt` | Lista de dependencias contiene `edge-tts>=7.3.1` |
| `uv.lock` | `edge-tts` actualizado y lock sincronizado con el manifiesto |
| `backend/services/auth/auth_service.py` | Solicitud OAuth y scopes requeridos de Twitch ampliados |
| `backend/config/locale_defaults.py` | Textos por defecto para los nuevos permisos |
| `locales/en.json` | Etiquetas en inglés de los permisos añadidos |
| `locales/es.json` | Etiquetas en español de los permisos añadidos |

---

## Verificación

- Se verificó que `uv.lock` resuelve `edge-tts` en `7.3.1` y declara el mínimo `>=7.3.1`.
- No se ejecutaron pruebas automatizadas.
- La corrección de Twitch requiere renovar la autorización en la aplicación para que el token incluya los scopes nuevos.
