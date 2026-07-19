# WT-1.4.2_03 - Sugerencias de Autocompletado, Coloración de Sintaxis Regex y Eliminación en Bloque

Hemos implementado un sistema avanzado de sugerencias y coloreado de variables en la interfaz del bot, así como la eliminación en bloque de tags y la limpieza del esquema de traducción redundante.

---

## Parte 1: Sugerencias y Autocompletado con `{`
- En los campos de entrada de respuestas del bot (tanto en el editor de comandos como en el editor emergente de mensajes de temporizadores), escribir `{` despliega un menú flotante con las variables disponibles: `{user}`, `{touser}` y `{random}`.
- La navegación en la caja de sugerencias se puede realizar con las teclas `Arriba/Abajo` e insertar el elemento presionando `Enter` o haciendo clic.

---

## Parte 2: Eliminación en Bloque de Tags
- Para que la edición de variables sea más fluida, si el usuario tiene el cursor al final de una variable (ej: justo después del carácter `}` de `{user}`) y presiona la tecla de borrar (`Backspace`), se borrará toda la variable de golpe en lugar de borrar letra por letra.
- Lo mismo ocurre si se presiona la tecla `Delete` estando al inicio de la variable (antes del carácter `{}`).

---

## Parte 3: Autocompletado y Coloreado de Sintaxis Regex
- Se ha integrado el widget `VariableTextEdit` en el campo `txt_regex` en la configuración avanzada de comandos.
- Al escribir `\`, se despliega un menú flotante con una lista descriptiva de expresiones y patrones comunes (ej: `\w (Letras/Dígitos)`, `\d (Dígitos)`, `(?:...) (Grupo sin captura)`).
- Al seleccionar una opción, se inserta únicamente el token de expresión correspondiente limpio (`\w`, `\d`, `(?:...)`).
- Los tokens regex se pintan automáticamente de color **ámbar en negrita (`#F59E0B`)** sin fondo, facilitando enormemente su lectura sobre el tema oscuro de la aplicación.
- Con esta incorporación interactiva de ayuda Regex, se eliminó el panel estático de ayuda lateral derecho, reduciendo el ancho del asistente de comandos de `700px` a un tamaño estándar de `520px`.

---

## Parte 4: Eliminación de Recursos I18n Obsoletos
- Al quitar el panel lateral de ayuda Regex, se eliminaron todas las claves de localización redundantes que empezaban con `regex_helper_` en:
  - `locales/es.json`
  - `locales/en.json`
  - `backend/config/default_en_locale.py`

---

## Verificación Realizada
- Ejecutamos `uv run python -m py_compile` sobre todos los archivos de diálogos y controles modificados.
- Validamos el inicio correcto del sistema ejecutando `uv run main.py`.
