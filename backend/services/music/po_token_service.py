# backend\services\music\po_token_service.py
"""Relevo entre quien necesita un PO token de YouTube y quien lo genera.

YouTube no sirve ciertos streams sin un token que pruebe que la petición viene de un navegador,
y generarlo exige un motor de navegador real. Este servicio no sabe qué es un navegador: el
proveedor de yt-dlp pide el token por un identificador (``binding``) y sigue sin esperar; el
generador toma esa petición, entrega el token y el proveedor lo recoge al renovar la URL.

Un fallo se anota contra el generador completo y no contra un binding, porque el identificador
puede ser la sesión o un video concreto. Así un navegador que Google no acepta no se reintenta
con cada pista nueva.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

KEEP_SECONDS = 6 * 60 * 60
SOONEST_SECONDS = 5.0
SLOWEST_SECONDS = 5 * 60.0
_MAX_DOUBLINGS = 16


@dataclass
class _Minted:
    token: str
    at: float


@dataclass
class _State:
    wanted: Optional[str] = None
    minted: Dict[str, _Minted] = field(default_factory=dict)
    failures: int = 0
    failed_at: Optional[float] = None
    warm: bool = False


def hold_seconds(failures: int) -> float:
    """Cuánto se deja en paz al generador tras ``failures`` fallos seguidos."""
    doublings = min(max(failures - 1, 0), _MAX_DOUBLINGS)
    return min(SOONEST_SECONDS * (1 << doublings), SLOWEST_SECONDS)


class PoTokenService:
    """Estado compartido del relevo: lo consulta el proveedor y lo alimenta el generador."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._state = _State()

    def token(self, binding: str) -> Optional[str]:
        """El token vigente de ``binding``; si no hay, anota la petición y devuelve ``None``."""
        with self._lock:
            fresh = self._fresh(binding)
            if fresh is not None:
                return fresh
            if not self._held():
                self._state.wanted = binding
            return None

    def minted(self, binding: str) -> Optional[str]:
        """Como ``token`` pero sin anotar nunca una petición."""
        with self._lock:
            return self._fresh(binding)

    def warm(self) -> bool:
        """Si el generador tiene una página ya atestiguada que responde en torno a un segundo."""
        with self._lock:
            return self._state.warm

    def set_warm(self, warm: bool) -> None:
        with self._lock:
            self._state.warm = warm

    def wanted(self) -> Optional[str]:
        """La petición pendiente, tomada y no leída: una petición produce un solo intento."""
        with self._lock:
            binding, self._state.wanted = self._state.wanted, None
            return binding

    def give(self, binding: str, token: str) -> None:
        """Guarda un token recién generado y olvida los fallos anteriores."""
        with self._lock:
            now = self._clock()
            self._state.minted = {
                key: item for key, item in self._state.minted.items() if now - item.at < KEEP_SECONDS
            }
            self._state.minted[binding] = _Minted(token, now)
            self._state.failures = 0
            self._state.failed_at = None

    def failed(self) -> None:
        """Anota un intento fallido: el siguiente espera ``hold_seconds`` según los fallos."""
        with self._lock:
            self._state.failures += 1
            self._state.failed_at = self._clock()

    def _fresh(self, binding: str) -> Optional[str]:
        item = self._state.minted.get(binding)
        if item is not None and self._clock() - item.at < KEEP_SECONDS:
            return item.token
        return None

    def _held(self) -> bool:
        failed_at = self._state.failed_at
        return failed_at is not None and self._clock() - failed_at < hold_seconds(self._state.failures)
