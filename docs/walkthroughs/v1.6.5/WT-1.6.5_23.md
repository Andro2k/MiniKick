# Walkthrough Técnico — MiniKick v1.6.5 (Paso 23)

Se consolidó el perfil del canal en la tarjeta de bienvenida y se eliminó la tarjeta de perfil que duplicaba esa información.

---

## Novedades

- Se agregaron badges de seguidores, fecha de creación, categoría, identificador, próximo horario y tipo de emisor cuando está disponible.
- Las cuentas Kick afiliadas muestran una corona junto al nombre.
- Se agregó un botón sobre el avatar para alternar entre los perfiles de Kick y Twitch, visible únicamente cuando ambas cuentas están conectadas.

## Mejoras

- El cambio de cuenta reutiliza la señal de selección de perfil existente para actualizar nombre, descripción, avatar y badges.
- Se conservó el acceso para abrir el canal y se retiraron los controles y estilos de la tarjeta antigua.
- La cantidad de columnas de badges se adapta al ancho del panel.
- Se retiraron claves de traducción y estilos que quedaron sin uso.

## Correcciones

- La tarjeta ya no deja visible información de una cuenta anterior al desconectarla o cambiar de perfil.
- El badge de afiliado solo aparece en canales Kick afiliados.

## Validación

- Se verificaron sintaxis, traducciones y auditoría estática del proyecto.
- La vista en ejecución no se validó visualmente en este entorno porque PySide6 no está disponible.
