# Walkthrough WT-1.5.8_37: Refactorización DRY de OAuth (BaseOAuthManager), Endurecimiento de Timeouts y Resolución Resiliente de Slugs en Kick

## 1. Contexto y Objetivos

Durante la auditoría de la integración de Kick y los servicios de autenticación en [`oauth_service.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py) y [`kick_client.py`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py), se identificaron varias oportunidades clave de mejora arquitectónica:
1. **Violación de DRY (Don't Repeat Yourself)**: [`KickAuthManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py) y [`TwitchAuthManager`](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py) repetían un 60% de código idéntico para consultar tokens, verificar autenticación, cerrar sesión y evaluar permisos (scopes) faltantes con operaciones de conjuntos (`set`).
2. **Ausencia de `timeout` en Peticiones HTTP de Kick Auth**: Las llamadas a `requests.post(KICK_TOKEN_URL, ...)` en `refresh_token()` y `_exchange_code()` no definían tiempo límite, arriesgando congelamientos indefinidos de hilos de ejecución ante latencia o caídas de `id.kick.com`.
3. **Resolución de Slugs en Canales de Kick con Guiones (`_` vs `-`)**:
   - En Kick, cuentas creadas con guión bajo (ej. `Pipe_Cabrales` o `rebeca_arenas`) tienen asignada oficialmente en la plataforma la URL `kick.com/pipe-cabrales` y `kick.com/rebeca-arenas`.
   - La API de Kick (`https://kick.com/api/v1/channels/{slug}`) responde con **HTTP 404** si se le pasa el nombre con guión bajo (`Pipe_Cabrales`), requiriendo obligatoriamente el slug con guión medio (`Pipe-Cabrales` o `pipe-cabrales`).
   - Se requería asegurar la conversión de `_` a `-` y dotar a `_fetch_channel_details` de una resolución inteligente de candidatos con fallback automático.

---

## 2. Cambios Implementados

### A. Capa de Autenticación ([backend/services/auth/oauth_service.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/oauth_service.py))
- **Extracción de `BaseOAuthManager`**:
  - Centraliza el constructor común `(client_id, client_secret, redirect_uri, storage, success_html_path)`.
  - Implementa de forma genérica:
    - `get_tokens(force=False) -> dict`
    - `is_authenticated() -> bool`
    - `logout() -> None`
    - `get_missing_scopes() -> list[str]` (evaluando `self.REQUIRED_SCOPES` contra los scopes del token parseados como `set`)
    - `has_missing_scopes() -> bool`
- **Refactorización de `KickAuthManager`**:
  - Hereda de `BaseOAuthManager`, reduciendo ~45 líneas de código duplicado.
  - Añadido `timeout=10` a las llamadas de red `requests.post(KICK_TOKEN_URL, ...)` en `refresh_token()` y `_exchange_code()`.
- **Refactorización de `TwitchAuthManager`**:
  - Hereda de `BaseOAuthManager`, reduciendo ~40 líneas de código duplicado.
  - Mantiene alias de retrocompatibilidad `REQUIRED_TWITCH_SCOPES = REQUIRED_SCOPES`.
  - Añadido `timeout=10` en `_exchange_code()`.

### B. Exportación de Paquete ([backend/services/auth/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/auth/__init__.py), [backend/services/__init__.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/services/__init__.py))
- Incorporado `BaseOAuthManager` a las listas `__all__` e importaciones de la capa de servicios para que módulos externos puedan tipar o extender gestores OAuth de forma limpia.

### C. Cliente de API de Kick ([backend/providers/chat/kick_client.py](file:///c:/Users/TheAn/Desktop/python/Kick/backend/providers/chat/kick_client.py))
- **Generación de Slug y Resolución Resiliente con Candidatos**:
  ```python
  def _generate_channel_slug(self, username: str) -> str:
      return username.strip().lstrip("@").replace("_", "-").replace(" ", "")
  ```
- **Fallback Automático en `_fetch_channel_details`**:
  ```python
  def _fetch_channel_details(self, slug: str, max_retries: int = 3) -> dict:
      slug_candidates = [slug]
      if "-" in slug:
          slug_candidates.append(slug.replace("-", "_"))
      elif "_" in slug:
          slug_candidates.append(slug.replace("_", "-"))
  ```
  - Si el primer candidato (`Pipe-Cabrales`) devuelve 200, retorna al instante en $\mathcal{O}(1)$.
  - Si devuelve 404, salta de inmediato sin reintentos inútiles al candidato alternativo (`Pipe_Cabrales`), garantizando resolución exitosa ante cualquier peculiaridad de la API de Kick.
- **Fail-safe de Timeouts**:
  - En `_request()`, se añadió `kwargs.setdefault("timeout", 10)` para asegurar que cualquier llamada REST tenga un límite determinista si no se especifica explícitamente.
  - En `_fetch_channel_details()`, se agregó `timeout=10` al `scraper.get(url)`.

---

## 3. Análisis Big-O & Principios de Diseño

* **DRY & SRP**: Centralización de la gestión del ciclo de vida del token y verificación de scopes en una sola entidad cohesiva.
* **Liskov Substitution Principle (LSP)**: Ambas clases derivadas (`KickAuthManager` y `TwitchAuthManager`) respetan exactamente el mismo contrato que sus versiones previas, garantizando que el contenedor de dependencias (`AppContainer`) y los workers (`KickAuthWorker`, `TwitchAuthWorker`) sigan funcionando de manera transparente.
* **Eficiencia Algorítmica**:
  - Comparación de permisos: $\mathcal{O}(S)$ donde $S \le 11$ es la cantidad fija de scopes requeridos, con búsquedas en $\mathcal{O}(1)$ sobre `set`.
  - Timeouts de red: Reduce de $\mathcal{O}(\infty)$ a $\mathcal{O}(1)$ acotado (máximo 10 segundos), evitando congelamientos en workers de Qt.

---

## 4. Verificación y Resultados

- **Compilación de Sintaxis**:
  ```bash
  uv run python -m py_compile backend/services/auth/oauth_service.py backend/services/auth/__init__.py backend/services/__init__.py backend/providers/chat/kick_client.py
  ```
  Resultado: 0 errores de compilación.

- **Pruebas en Vivo de Slugs de Kick**:
  - `pipe-cabrales` -> HTTP 200 (resuelto exitosamente).
  - `Pipe_Cabrales` -> HTTP 404 (confirmando que Kick exige guión medio `-`).
  - `rebeca-arenas` -> HTTP 200 vs `rebeca_arenas` -> HTTP 404.

- **Pruebas de Autenticación Específicas**:
  ```bash
  uv run pytest resources/tests/unit/providers/test_kick_auth.py resources/tests/unit/providers/test_twitch_auth.py
  ```
  Resultado: `13/13 passed in 0.12s (100%)`.
