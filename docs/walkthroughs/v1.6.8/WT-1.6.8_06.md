# Walkthrough Técnico — MiniKick v1.6.8 (Paso 06)

La vista previa de video carga a la primera: se calienta WebEngine, se reintenta si el reproductor no responde y un ocultado breve ya no la descarga.

---

## Mejoras

- **Calentamiento:** la primera vez que se muestra el Reproductor, 1,5 s después, `MusicVideoPreviewPanel.warm_up()` carga los módulos de WebEngine y el perfil por defecto. Así el primer ▶ no congela la ventana mientras se cargan las DLL de Chromium.
- **Señal de listo:** el reproductor de YouTube avisa con `onReady` (título `mk-yt-ready`). Si no avisa en 8 s, el panel recrea la vista y reintenta una vez; si vuelve a fallar, muestra el mensaje con el botón **Abrir en el navegador**.
- **Descarga con gracia:** ocultar el panel descarga la vista solo si sigue oculto 300 ms después (`HIDE_GRACE_MS`). Un ocultado breve, como un parpadeo al recrearse la ventana, ya no cierra la vista previa.
- **Diagnóstico:** el log registra `Loading`, `Player ready in N ms`, el reintento y el fallo definitivo (`[MusicVideo]`).

## Limitaciones conocidas

- La causa exacta del "pantallazo" no se pudo reproducir sin pantalla en Linux. Si persiste, el log dirá si el reproductor tardó en estar listo (`Player ready in N ms`) o si hizo falta el reintento.
- La caché (`%LOCALAPPDATA%\.Minikick\cache`) guarda solo audio (`bestaudio/best`), por eso la vista previa sigue usando el embed de YouTube y no un archivo local.
