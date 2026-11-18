# backend\interfaces\po_token_interface.py
"""Contratos del generador de PO tokens de YouTube y de la página de navegador que los produce."""

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass(frozen=True)
class PoTokenAnswer:
    """Lo que la página respondió para un binding: un token o el motivo del fallo."""

    binding: str
    token: Optional[str] = None
    error: Optional[str] = None


class IPoTokenMintQueue(Protocol):
    """Lo que el generador necesita del relevo: qué se pide y dónde dejar el resultado."""

    def wanted(self) -> Optional[str]: ...

    def give(self, binding: str, token: str) -> None: ...

    def failed(self) -> None: ...

    def set_warm(self, warm: bool) -> None: ...


class IPoTokenPage(Protocol):
    """Una página de navegador capaz de generar tokens, sin saber qué motor la ejecuta."""

    def ask(self, binding: str) -> None: ...

    def answer(self) -> Optional[PoTokenAnswer]: ...

    def close(self) -> None: ...
