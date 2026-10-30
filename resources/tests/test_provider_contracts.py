# resources\tests\test_provider_contracts.py

import ast
import inspect
import textwrap

import pytest

from backend.interfaces import IMusicProvider, ITTSProvider
from backend.providers.music.youtube_provider import YouTubeMusicProvider
from backend.providers.voices.local_provider import LocalTTSProvider
from backend.providers.voices.online_provider import WebTTSProvider
from backend.providers.voices.piper_provider import PiperTTSProvider


def _protocol_methods(protocol: type) -> dict[str, inspect.Signature]:
    return {
        name: inspect.signature(member)
        for name, member in vars(protocol).items()
        if inspect.isfunction(member) and not name.startswith("_")
    }


def _protocol_attributes(protocol: type) -> set[str]:
    return {name for name in getattr(protocol, "__annotations__", {}) if not name.startswith("_")}


def _declared_members(cls: type) -> set[str]:
    members = set(vars(cls))
    tree = ast.parse(textwrap.dedent(inspect.getsource(cls)))
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                members.add(target.attr)
    return members


def _params(signature: inspect.Signature) -> list[inspect.Parameter]:
    return [p for name, p in signature.parameters.items() if name != "self"]


def _assert_signature_compatible(owner: str, name: str, expected: inspect.Signature, actual: inspect.Signature) -> None:
    exp, act = _params(expected), _params(actual)
    assert len(act) >= len(exp), f"{owner}.{name}: faltan parámetros ({len(act)} < {len(exp)})"

    for e, a in zip(exp, act):
        assert e.name.lstrip("_") == a.name.lstrip("_"), (
            f"{owner}.{name}: parámetro '{a.name}' no coincide con '{e.name}' del contrato"
        )
        assert e.kind == a.kind, f"{owner}.{name}: '{a.name}' cambia el tipo de parámetro"

    for extra in act[len(exp):]:
        assert extra.default is not inspect.Parameter.empty or extra.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ), f"{owner}.{name}: el parámetro extra '{extra.name}' debe tener valor por defecto"


def _assert_implements(protocol: type, cls: type) -> None:
    owner = cls.__name__
    for name, expected in _protocol_methods(protocol).items():
        member = getattr(cls, name, None)
        assert callable(member), f"{owner} no implementa {protocol.__name__}.{name}"
        _assert_signature_compatible(owner, name, expected, inspect.signature(member))

    declared = _declared_members(cls)
    for attr in _protocol_attributes(protocol):
        assert attr in declared, f"{owner} no declara el atributo '{attr}' de {protocol.__name__}"


def test_music_protocol_declares_the_api_the_code_uses():
    methods = set(_protocol_methods(IMusicProvider))
    assert {
        "add_to_queue", "get_current_song", "get_queue", "remove_from_queue", "move_in_queue",
        "skip_current", "pause_playback", "resume_playback", "seek", "set_volume", "set_ducking", "shutdown",
    } <= methods
    assert _protocol_attributes(IMusicProvider) == {"queue_updated", "resolve_error_occurred", "auto_resume"}


def test_youtube_music_provider_fulfils_music_contract():
    _assert_implements(IMusicProvider, YouTubeMusicProvider)


@pytest.mark.parametrize("provider_cls", [PiperTTSProvider, WebTTSProvider, LocalTTSProvider])
def test_tts_providers_fulfil_tts_contract(provider_cls):
    _assert_implements(ITTSProvider, provider_cls)


def test_contract_check_detects_divergence():
    class Broken:
        def get_queue(self, extra):
            return []

    expected = _protocol_methods(IMusicProvider)["get_queue"]
    with pytest.raises(AssertionError):
        _assert_signature_compatible("Broken", "get_queue", expected, inspect.signature(Broken.get_queue))
