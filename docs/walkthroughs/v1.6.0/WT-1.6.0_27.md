# Walkthrough v1.6.0_27: Integración de Insignia de Plataforma en Avatar Circular y Expansión de Ancho de Chat a 500px

## Novedades

1. **Insignia de Plataforma en el Círculo de Perfil**:
   - Se trasladó el indicador de plataforma (Kick, Twitch, YouTube, TikTok) al círculo de avatar, posicionándolo como una micro-insignia flotante en la esquina inferior derecha del avatar (`.avatar-badge.avatar-platform-*`).
   - Se eliminó el badge redundante de plataforma en el encabezado del mensaje (`header-left`), logrando que la primera línea de texto comience de forma limpia directamente con las insignias de canal (Streamer, VIP, Moderador, Subcriptor, Nivel) seguidas por el nombre de usuario y la hora `[HH:MM]`.
   - Se respetó de forma estricta el conmutador de visibilidad `show_platform`: si la opción está desactivada, la insignia no se dibuja; si está activada, se renderiza en el avatar con su respectivo gradiente de marca (`#53FC18` para Kick, `#9146FF` para Twitch, `#EF4444` para YouTube, gradiente cyan-magenta para TikTok).

## Mejoras

1. **Expansión del Límite de Ancho a 500px**:
   - Se incrementó el `max-width` de `.message-box` de 440px a 500px en `assets/overlays/chat/css/dark.css`, `assets/overlays/chat/css/light.css` y `assets/overlays/chat/chat.html`.
   - Se actualizó el límite de GIFs en orientación horizontal a `max-width: min(500px, 70vw) !important;`.
   - Permite a los streamers configurar anchos de fuente de navegador en OBS Studio de hasta 500px sin que las burbujas de chat queden recortadas o limitadas artificialmente a 440px.

2. **Fidelidad del Mockup Visual en Panel de Configuración**:
   - Se actualizó `ChatOverlayMockupWidget` en `frontend/components/chat/chat_mockup.py` para reflejar la insignia de plataforma en la esquina del avatar y dibujar las insignias de rol en el encabezado junto al nombre de usuario.
   - Cálculo dinámico de ancho en píldoras horizontales ajustado a `show_badges`.
   - Se eliminó el parámetro huérfano `badge_type` en `_draw_avatar`, certificado con 0 incidencias en el auditor AST.

## Correcciones

1. **Resolución de Error de Sintaxis de JavaScript en `chat.js`**:
   - Corrección de `SyntaxError` ("Identifier 'platform' has already been declared") producido por una doble declaración de `const platform` dentro de la función `addMessage`.

---

### Verificación y Pruebas Realizadas
- `uv run pytest resources/tests/`: 50/50 pruebas superadas con 100% de éxito.
- `resources/tools/unused_parameter_manager.py`: 0 hallazgos detectados.
- `resources/tools/dead_code_manager.py`: 0 hallazgos detectados.
- `resources/tools/role_manager.py -v`: 0 estilos o roles faltantes/huérfanos.
