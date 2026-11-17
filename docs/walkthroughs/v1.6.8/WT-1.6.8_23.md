# Walkthrough Técnico — MiniKick v1.6.8 (Paso 23)

El i18n deja los JSON anidados (`assets/locales/{en,es}.json`) y pasa a archivos Fluent (`assets/i18n/<lang>/main.ftl`), siguiendo el enfoque de sonora (`crates/i18n`: un `main.ftl` por idioma, bundle perezoso, respaldo en inglés). El motivo principal son los plurales correctos: Fluent los resuelve con selectores `[one]/*[other]` y se acaban los sufijos `(s)`. El cambio se entregó en parches atómicos (dependencia, servicio, `.ftl` como fuente, plurales y migración de llamadores a `kwargs`); este documento los cierra.

---

## Novedades

- **Archivos `.ftl` como fuente de las traducciones:** `assets/i18n/en/main.ftl` y `assets/i18n/es/main.ftl` (1418 mensajes cada uno). Las claves anidadas `a.b.c` son ids planos `a-b-c` y las variables se escriben `{ $nombre }`. El código sigue llamando `i18n.get("a.b.c", ...)`.
- **Plurales de Fluent:** 7 mensajes en `en` y 9 en `es` usan selectores: paginación de logs, cooldown, límite y posición inválida de la cola de música, aviso de archivos faltantes y contador de muertes. Ejemplo: `{ $count -> [one] song *[other] songs }`.
- **Valores por `kwargs`:** `get(clave, user=user, count=n)` reemplaza a `get(clave).replace("{user}", user)` en todo `backend/` y `frontend/`.
- **Dependencia:** `fluent.runtime>=0.4.0` (arrastra `fluent-syntax`, `babel` y `pytz`), declarada en `pyproject.toml`, `requirements.in`, `requirements.txt` y `uv.lock`.

## Cambios por capa

- **Servicios (`backend/services/settings/translation_service.py`):**
  - Un bundle por archivo, cacheado a nivel de módulo y compartido entre instancias (parsear un idioma cuesta ~130 ms y hay varios `TranslationService()` de respaldo).
  - Resolución: idioma activo → inglés → la propia clave. El aviso de clave faltante o de error de formato sale una sola vez.
  - Compatibilidad con el `str.format` anterior: los enteros se pasan a Fluent sin separador de miles (si no, `12345` sale como `12.345` en español) y el resto de valores como texto. Las variables sin valor quedan como `{nombre}` literal.
  - Un idioma sin `.ftl` usa el inglés; el servicio ya no escribe archivos. `load_language` y `current_lang` se mantienen.
- **Configuración (`backend/config`):** se retira `locale_defaults.py` (`DEFAULT_DICTIONARY`, 1804 líneas) y su exportación; solo servía a la autorreparación del servicio.
- **Backend (controladores, handlers, workers y providers):** 91 llamadas `get(...).replace("{x}", ...)` pasan a `kwargs` (12 en `music_handler` y 79 en el resto), incluidas las de clave dinámica y la de `systts`. Se quitaron tres kwargs heredados que el mensaje ya no usaba (`vol`, `count` en `msg_reset` y `platform` en `updated_local_saved_api_failed`).
- **Frontend (vistas, componentes, diálogos y ventana principal):** 49 llamadas pasan a `kwargs`, incluidos los casos en dos pasos (`plantilla = get(...)` y luego `plantilla.replace(...)`). Los mensajes con número (paginación de logs, archivos faltantes) reciben el entero real para que el plural se decida bien.
- **Herramientas:** `project_translation_integrity_auditor.py` lee los `.ftl` (aplana ids a `a.b.c`, toma la variante por defecto de los selectores) y borra las claves sobrantes por rango sin reformatear el archivo; reconoce `.ftl` como extensión de archivo. El generador JSON→FTL solo existió mientras el JSON era la fuente y se retiró.
- **Tests:** `test_locales_ftl.py` (sintaxis y paridad de claves y variables entre idiomas), `test_translation_service.py` (servicio, números, plurales reales), `test_translation_integrity_auditor.py` y `test_i18n_call_arguments.py` (ver Verificación). Los dobles de i18n de los tests aceptan `**kwargs` como el servicio real y, cuando devolvían plantillas con variables, las sustituyen.
- **Documentación y reglas:** `README.md`, `.agents/rules/minikick.md` y `.agents/skills/minikick-quality-auditor/SKILL.md` apuntan a los `.ftl`.

## Archivos afectados

- **Nuevos:** `assets/i18n/{en,es}/main.ftl`, `resources/tests/test_translation_service.py`, `resources/tests/test_translation_integrity_auditor.py`, `resources/tests/test_i18n_call_arguments.py`.
- **Eliminados:** `assets/locales/en.json`, `assets/locales/es.json`, `backend/config/locale_defaults.py`.
- **Modificados:** `translation_service.py`, `backend/config/__init__.py`, los controladores, handlers, workers y providers de `backend/` y las vistas, componentes y diálogos de `frontend/` que llamaban a `get(...).replace(...)`, el auditor de claves, `project_quality_suite.py`, `resources/tools/README.md`, los tests citados, `pyproject.toml`, `requirements.in`, `requirements.txt`, `uv.lock`, `README.md` y los dos archivos de `.agents`.

## Cómo usarlo

Para agregar un texto, escribe el mismo id en los dos `main.ftl` y llámalo con `kwargs`:

```
chat-welcome = Hola { $user }, tienes { $count } { $count ->
    [one] mensaje
   *[other] mensajes
}.
```

```python
self.i18n.get("chat.welcome", user=user, count=n)
```

No uses `.replace("{x}", ...)` sobre el resultado de `get`. Pasa siempre las variables por `kwargs` y el entero real cuando el mensaje tiene plural.

## Verificación

- Antes de retirar los JSON se comparó la salida de las 1415 claves de entonces en `es` y `en` con la del JSON anterior (`str.format`), con y sin `kwargs`: coincidían todas.
- `test_i18n_call_arguments.py` recorre por AST `backend/` y `frontend/` y comprueba que cada `get("clave", nombre=valor)` con clave literal pase exactamente las variables del mensaje. Es la guardia principal: como las variables sin valor quedan como `{nombre}`, un kwarg mal escrito no daría error. Con ella se encontraron y quitaron los kwargs heredados que sobraban.
- `test_translation_service.py` cubre claves con puntos, respaldo en inglés, aviso único, números sin separador, variables sin valor, que cada clave real se resuelva y 22 casos de plural de mensajes reales (1 frente a 0/5).
- Estado final: 425 pruebas aprobadas. En la suite de calidad pasan Translation Keys, Dead Code y Hardcoded Text; solo fallan Frontend QSS Roles y Frontend Qt Windows, que ya fallaban antes de esta migración.

## Limitaciones conocidas

- Las llamadas con clave dinámica (`get(msg_key, ...)`) no las revisa `test_i18n_call_arguments.py`, que solo mira claves literales. Sus nombres de variable se conservaron tal cual estaban en el `.replace` original.
- Quedan 12 líneas con `.replace("{x}", ...)` que no son de i18n y se dejaron a propósito: plantilla HTML y URL de `auth_service`, URL de miniaturas de Twitch, plantillas de comandos y widgets escritas por el usuario, `_get_text` del worker de crash, la plantilla de alerta de `alert_mockup` y el formato de `table_widget`.
- Siguen con `(s)` las etiquetas sin cantidad (`Platform(s)`, `event(s)`, `Duration (s)`), porque no hay un número del que decidir el plural.
- Si falta `en/main.ftl`, la interfaz mostraría las claves: ya no se recrea desde `DEFAULT_DICTIONARY`. En el ejecutable empaquetado `assets` va dentro del bundle, así que no debería ocurrir.
- `fluent.runtime` 0.4.0 es de 2021 y no hay versión más reciente. Cada idioma nuevo necesita su carpeta `assets/i18n/<lang>/main.ftl`; el test de paridad avisa de claves o variables que falten respecto a `en`.
