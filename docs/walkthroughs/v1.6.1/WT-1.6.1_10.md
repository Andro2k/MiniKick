# Walkthrough WT-1.6.1_10: Opción Configurable para Incluir Comandos en Top Chatters

## Novedades

* **Casilla de Configuración para Incluir Comandos en Top Chatters:**
  Se integró una nueva opción configurable mediante casilla de verificación (`QCheckBox`) en la tarjeta del widget de Top Chatters en [`frontend/components/widgets/widget_card.py`](file:///c:/Users/TheAn/Desktop/python/Kick/frontend/components/widgets/widget_card.py):  
  *«Incluir comandos en el conteo (!)»* (`widgets.chatters.include_commands_label`).  
  Por defecto, permanece desmarcada para proteger la integridad del ranking contra spam de comandos, pero permite al streamer activarla con un clic si desea que los comandos sumen al total de mensajes de sus espectadores.

* **Evaluación Dinámica de Comandos en el Motor de Ingesta:**
  En [`WidgetsController._record_chatter_message`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/controllers/widgets_controller.py), se reemplazó el descarte estático de comandos por una consulta $\mathcal{O}(1)$ a la configuración del widget (`include_commands`). Si la opción está habilitada, cualquier mensaje válido comenzando con `!` se contabiliza de inmediato para el podio de chatters; si está deshabilitada, se preserva el filtro tradicional sin alterar el rendimiento.

## Mejoras

* **Protección Firme contra Bots Incondicional:**
  A pesar de que el streamer habilite la inclusión de comandos, las respuestas y saludos automáticos de bots oficiales del sistema (`_IGNORED_CHATTER_BOTS`) y cuentas con insignia `bot` continúan siendo filtrados de manera estricta para evitar adulteraciones en el podio.

* **Paridad Lingüística Completa e i18n:**
  Se añadieron las cadenas descriptivas en [`locales/es.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/es.json) y [`locales/en.json`](file:///c:/Users/TheAn/Desktop/python/Kick/locales/en.json), superando todas las auditorías del verificador anti-hardcode sin ninguna cadena huérfana.

## Correcciones

* **Flexibilidad en Canales con Dinámicas de Minijuegos:**
  Se corrigió la limitación rígida donde los espectadores que participaban activamente mediante comandos del canal quedaban completamente invisibilizados del Top Chatters, otorgándole al streamer el control total sobre las reglas de participación de su comunidad.
