# backend\config\webhook_endpoint_store.py

import logging
import threading
from typing import Sequence

from backend.interfaces import IConfigProvider, SecretCipher, TokenEncryptionError
from backend.interfaces.i_webhooks import DEFAULT_PLATFORMS, WebhookEndpointConfig
from backend.utils import fast_dumps, fast_loads

logger = logging.getLogger("minikick.config.webhook_endpoints")

CONFIG_KEY = "webhook_endpoints"
_ENCRYPTED_PREFIX = "enc:v1:"


class WebhookEndpointStore:
    def __init__(self, config: IConfigProvider, cipher: SecretCipher) -> None:
        self._config = config
        self._cipher = cipher
        self._lock = threading.Lock()
        self._active: tuple[WebhookEndpointConfig, ...] | None = None

    def load_all(self) -> list[WebhookEndpointConfig]:
        return [endpoint for _, endpoint in self._decode_records() if endpoint is not None]

    def save_all(self, endpoints: Sequence[WebhookEndpointConfig]) -> None:
        new_ids = {endpoint.endpoint_id for endpoint in endpoints}
        records = [self._to_record(endpoint) for endpoint in endpoints]
        records.extend(
            record for record, endpoint in self._decode_records()
            if endpoint is None and isinstance(record, dict) and record.get("endpoint_id") not in (None, *new_ids)
        )
        self._config.save_string(CONFIG_KEY, fast_dumps(records))
        with self._lock:
            self._active = None

    def active(self) -> tuple[WebhookEndpointConfig, ...]:
        with self._lock:
            if self._active is None:
                self._active = tuple(ep for ep in self.load_all() if ep.enabled)
            return self._active

    def _decode_records(self) -> list[tuple[object, WebhookEndpointConfig | None]]:
        raw = self._config.load_string(CONFIG_KEY, "") or ""
        if not raw.strip():
            return []
        try:
            records = fast_loads(raw)
        except ValueError as err:
            logger.error("[WebhookStore] Stored endpoints are not valid JSON; ignoring them: %s", err)
            return []
        return [(record, self._from_record(record)) for record in records] if isinstance(records, list) else []

    def _to_record(self, endpoint: WebhookEndpointConfig) -> dict:
        return {
            "endpoint_id": endpoint.endpoint_id,
            "name": endpoint.name,
            "formatter": endpoint.formatter,
            "events": sorted(endpoint.events),
            "platforms": sorted(endpoint.platforms),
            "enabled": endpoint.enabled,
            "target_url": self._seal("target_url", endpoint.target_url),
            "hmac_secret": self._seal("hmac_secret", endpoint.hmac_secret) if endpoint.hmac_secret else "",
        }

    def _from_record(self, record: dict) -> WebhookEndpointConfig | None:
        try:
            endpoint_id = str(record["endpoint_id"])
            name = str(record.get("name", endpoint_id))
            target_url = self._open(str(record["target_url"]))
            hmac_secret = self._open(str(record.get("hmac_secret", "")))
            return WebhookEndpointConfig(
                endpoint_id=endpoint_id,
                name=name,
                target_url=target_url,
                formatter=str(record.get("formatter", "generic")),
                events=frozenset(record.get("events", ())),
                platforms=frozenset(record.get("platforms", DEFAULT_PLATFORMS)),
                hmac_secret=hmac_secret,
                enabled=bool(record.get("enabled", True)),
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            logger.error("[WebhookStore] Skipping a malformed endpoint record.")
        except Exception:
            name = record.get("name", "?") if isinstance(record, dict) else "?"
            logger.error("[WebhookStore] Could not decrypt endpoint '%s' (different Windows user/profile?). Skipped.", name)
        return None

    def _seal(self, field: str, value: str) -> str:
        try:
            return _ENCRYPTED_PREFIX + self._cipher.encrypt(value)
        except Exception as err:
            logger.error("[WebhookStore] Could not encrypt '%s'; nothing was saved: %s", field, type(err).__name__)
            raise TokenEncryptionError(f"Could not encrypt '{field}'") from err

    def _open(self, value: str) -> str:
        if value.startswith(_ENCRYPTED_PREFIX):
            return self._cipher.decrypt(value[len(_ENCRYPTED_PREFIX):])
        return value
