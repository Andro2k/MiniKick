# resources\tests\test_webhook_endpoint_store.py

import base64

import pytest

from backend.config.toml_config_provider import TomlConfigProvider
from backend.config.webhook_endpoint_store import WebhookEndpointStore
from backend.interfaces import TokenEncryptionError
from resources.tests._webhook_helpers import make_endpoint

URL = "https://discord.com/api/webhooks/123456/SECRET-token_abc"


class ReversibleCipher:
    def encrypt(self, plaintext):
        return base64.b64encode(plaintext.encode()).decode()

    def decrypt(self, ciphertext):
        return base64.b64decode(ciphertext.encode()).decode()


class BrokenCipher:
    def encrypt(self, plaintext):
        raise OSError("dpapi unavailable")

    def decrypt(self, ciphertext):
        raise OSError("different user")


def _store(tmp_path, cipher=None):
    return WebhookEndpointStore(TomlConfigProvider(tmp_path / "config.toml"), cipher or ReversibleCipher())


def test_round_trip_through_toml_keeps_every_field(tmp_path):
    endpoint = make_endpoint("ep1", target_url=URL, formatter="discord", hmac_secret="k", platforms=frozenset({"kick"}))
    _store(tmp_path).save_all([endpoint])
    assert _store(tmp_path).load_all() == [endpoint]


def test_url_and_secret_are_not_stored_in_plaintext(tmp_path):
    _store(tmp_path).save_all([make_endpoint(target_url=URL, hmac_secret="topsecret-hmac")])
    raw = (tmp_path / "config.toml").read_text(encoding="utf-8")
    assert "SECRET-token_abc" not in raw and "topsecret-hmac" not in raw
    assert "enc:v1:" in raw


def test_active_returns_only_enabled_endpoints_and_refreshes_on_save(tmp_path):
    store = _store(tmp_path)
    store.save_all([make_endpoint("on"), make_endpoint("off", enabled=False)])
    assert [ep.endpoint_id for ep in store.active()] == ["on"]
    store.save_all([make_endpoint("other")])
    assert [ep.endpoint_id for ep in store.active()] == ["other"]


def test_undecryptable_endpoints_are_skipped_not_fatal(tmp_path):
    _store(tmp_path).save_all([make_endpoint(target_url=URL)])
    assert _store(tmp_path, BrokenCipher()).load_all() == []


def test_failed_encryption_raises_and_saves_nothing(tmp_path):
    store = _store(tmp_path, BrokenCipher())
    with pytest.raises(TokenEncryptionError):
        store.save_all([make_endpoint(target_url=URL)])
    assert not (tmp_path / "config.toml").exists()


def test_corrupt_json_yields_no_endpoints(tmp_path):
    provider = TomlConfigProvider(tmp_path / "config.toml")
    provider.save_string("webhook_endpoints", "{not json")
    assert WebhookEndpointStore(provider, ReversibleCipher()).load_all() == []


class DecryptFailsCipher(ReversibleCipher):
    def decrypt(self, ciphertext):
        raise OSError("different user")


def test_unreadable_endpoints_survive_saves_made_by_another_profile(tmp_path):
    _store(tmp_path).save_all([make_endpoint("mine", target_url=URL)])
    other = _store(tmp_path, DecryptFailsCipher())
    assert other.load_all() == []
    other.save_all([make_endpoint("new", target_url="https://example.test/h")])
    assert [ep.endpoint_id for ep in _store(tmp_path).load_all()] == ["new", "mine"]


def test_unreadable_record_is_replaced_when_the_same_id_is_saved_again(tmp_path):
    _store(tmp_path).save_all([make_endpoint("same", target_url=URL)])
    other = _store(tmp_path, DecryptFailsCipher())
    other.save_all([make_endpoint("same", target_url="https://example.test/new")])
    loaded = _store(tmp_path).load_all()
    assert [(ep.endpoint_id, ep.target_url) for ep in loaded] == [("same", "https://example.test/new")]
