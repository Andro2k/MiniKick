# Walkthrough Técnico — MiniKick v1.6.8 (Paso 30)

Se añadió a la música de YouTube un sistema de PO tokens inspirado en `sonorahq/sonora` (`crates/state/src/potoken.rs`, `potoken.js` y `crates/music/src/potoken.rs`). YouTube exige un token que pruebe que la petición viene de un navegador real para ciertos streams; los clientes web de yt-dlp (`web`, `mweb`, `tv`) fallaban sin él ("Sign in to confirm you're not a bot"). Ahora una página oculta de QtWebEngine genera esos tokens y yt-dlp los recibe por su framework de proveedores.

---

## Cómo funciona

1. yt-dlp pide un token para un identificador (`binding`: sesión de visitante o video) a `MiniKickPTP`.
2. `MiniKickPTP` consulta `PoTokenService`. Si no hay token vigente, deja **una** petición pendiente y espera: 2 s si el navegador está caliente, 15 s si arranca.
3. `PoTokenCoordinator` (Qt) llama a `PoTokenMinter.tick()` con un `QTimer`. El minter toma la petición, abre una página `QWebEnginePage` sin vista y silenciada, y esta pide el token al cliente de atestiguado de YouTube con un script propio.
4. El token vuelve por `runJavaScript`, se guarda 6 h en el servicio y el proveedor lo recoge. La página queda caliente 20 s para las pistas siguientes y luego se cierra.
5. Un fallo (error, timeout, motor no disponible) hace que el servicio no acepte nuevas peticiones durante 5 s, y el doble en cada fallo seguido hasta 5 min.

## Cambios por capa

**Backend**
- `services/music/po_token_service.py`: relevo con tokens vigentes por binding, una petición pendiente y espera con backoff.
- `services/music/po_token_minter_service.py`: máquina de estados pura que atiende las peticiones con una página, sin dependencia de Qt.
- `interfaces/po_token_interface.py`: `IPoTokenSource`, `IPoTokenMintQueue`, `IPoTokenPage` y `PoTokenAnswer`.
- `providers/music/youtube_po_token_provider.py`: `MiniKickPTP`, proveedor de yt-dlp. Solo responde a clientes web; `ios` y `android` nunca lo consultan, así que su camino rápido no espera.
- `workers/music_worker.py`: `YouTubeResolveWorker` acepta `ytdlp_setup`, que corre tras importar yt-dlp. El worker no conoce los PO tokens.
- `providers/music/youtube_music_provider.py`: registra el proveedor en el hilo del worker; si falla, la resolución sigue sin token.
- `core/app_container_core.py`: crea `po_token_service` y lo entrega al proveedor de música.

**Frontend**
- `window/po_token_coordinator.py`: `WebEnginePoTokenPage` (página sin vista, silenciada, perfil no persistente, script inyectado) y `PoTokenCoordinator`.
- `window/composition_coordinator.py` y `window/shutdown_coordinator.py`: se crea al componer la ventana y se detiene antes de cerrar la música.

## Diferencias con Sonora

- El resultado vuelve por `runJavaScript`; no hace falta la cookie `SONORA_POT`.
- El script es propio: busca el cliente que expone `wpc` recorriendo `window`, no depende de nombres ofuscados fijos.
- Sonora no espera nunca porque cae a un token de arranque en frío. yt-dlp liga cada extracción a un binding nuevo, así que aquí la petición sí espera al navegador.

## Verificación

| Comprobación | Resultado |
| --- | --- |
| `pytest resources/tests` | 498 aprobadas |
| Script de la página, en Node con un cliente simulado | Mina con el binding de la URL, atiende un segundo binding y reintenta ante `SDF:notready` |
| Director real de yt-dlp (2026.10.26) con el proveedor registrado | Devuelve el token para `WEB` y nada para `IOS` |
| `project_architecture_boundary_auditor.py` y de ubicación de archivos | Sin violaciones |
| `project_quality_suite.py --quick` | Los mismos 2 fallos que antes del cambio (roles QSS sin uso y ventanas fantasma de `ModernButton`) |
| `ruff` sobre lo nuevo | Sin errores |

## Pendiente de probar en Windows

- Que `QWebEnginePage` sin vista complete el atestiguado de YouTube y que `runJavaScript` devuelva el token; no se pudo comprobar donde se desarrolló (sin `QtWebEngineCore`).
- Que una pista que antes fallaba en `web`/`mweb` se resuelva, y cuánto tarda la primera con el navegador frío (límite 15 s).
- Peticiones simultáneas: el relevo guarda una sola petición pendiente, así que dos workers que pidan a la vez pueden pisarse; el reintento del worker lo cubre.
- El framework de proveedores de yt-dlp es reciente; si una versión futura cambia sus módulos, el registro falla con un log y la música sigue sin PO token.
