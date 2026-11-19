# backend\services\music\po_token_minter_service.py
"""Máquina de estados que atiende las peticiones de PO token con una página de navegador.

No dibuja ni programa nada: quien la use llama a ``tick()`` y espera el tiempo que devuelve. Una
petición del relevo abre una página; esa página, una vez que genera un token, queda "caliente" y
atiende las siguientes peticiones sin recargarse hasta que pasa ``LINGER_SECONDS`` sin uso. Un
token vive más que la página que lo generó, y una página abierta pesa cientos de MiB.
"""

import logging
import time
from typing import Callable, Optional, Tuple

from backend.interfaces import IPoTokenMintQueue, IPoTokenPage

logger = logging.getLogger(__name__)

PATIENCE_SECONDS = 45.0
ANSWER_SECONDS = 10.0
LINGER_SECONDS = 20.0
IDLE_TICK_SECONDS = 0.5
BUSY_TICK_SECONDS = 0.1

PageFactory = Callable[[str], IPoTokenPage]


class PoTokenMinter:
    def __init__(
        self,
        queue: IPoTokenMintQueue,
        open_page: PageFactory,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._queue = queue
        self._open_page = open_page
        self._clock = clock
        self._page: Optional[IPoTokenPage] = None
        self._warm = False
        self._asked: Optional[Tuple[str, float]] = None
        self._used = 0.0

    def tick(self) -> float:
        """Avanza un paso y devuelve los segundos que conviene esperar hasta el siguiente."""
        if self._page is None:
            self._start()
        elif self._asked is not None:
            self._carry()
        else:
            self._ask()
        return BUSY_TICK_SECONDS if self._page is not None else IDLE_TICK_SECONDS

    def close(self) -> None:
        """Cierra la página y avisa de que el generador ya no está caliente."""
        page, self._page = self._page, None
        self._asked = None
        self._warm = False
        if page is not None:
            try:
                page.close()
            except Exception:
                logger.exception("[PoToken] Error closing the minting page")
        self._queue.set_warm(False)

    def _start(self) -> None:
        binding = self._queue.wanted()
        if binding is None:
            return
        try:
            self._page = self._open_page(binding)
        except Exception as error:
            logger.warning("[PoToken] Cannot open the minting page: %s", error)
            self._queue.failed()
            return
        logger.debug("[PoToken] Minting a token")
        now = self._clock()
        self._asked = (binding, now)
        self._used = now

    def _ask(self) -> None:
        if self._clock() - self._used > LINGER_SECONDS:
            logger.debug("[PoToken] Nothing more to mint, closing the minting page")
            self.close()
            return
        binding = self._queue.wanted()
        if binding is None:
            return
        self._page.ask(binding)
        self._asked = (binding, self._clock())

    def _carry(self) -> None:
        binding, asked_at = self._asked
        answer = self._page.answer()
        if answer is not None and answer.binding == binding:
            if answer.error is not None:
                logger.warning("[PoToken] The page could not mint a token: %s", answer.error)
                self._fail()
                return
            if answer.token:
                self._finish(binding, answer.token, asked_at)
                return
        patience = ANSWER_SECONDS if self._warm else PATIENCE_SECONDS
        if self._clock() - asked_at > patience:
            logger.warning("[PoToken] The minting page did not answer in %.0f s", patience)
            self._fail()

    def _finish(self, binding: str, token: str, asked_at: float) -> None:
        logger.debug("[PoToken] Minted a token in %.1f s", self._clock() - asked_at)
        self._warm = True
        self._asked = None
        self._used = self._clock()
        self._queue.give(binding, token)
        self._queue.set_warm(True)

    def _fail(self) -> None:
        self.close()
        self._queue.failed()
