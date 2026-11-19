# backend\providers\music\youtube_po_token_provider.py
"""Proveedor de PO tokens para yt-dlp respaldado por el relevo de MiniKick.

yt-dlp pide el token por el identificador al que YouTube lo liga (``binding``). Aquí no se genera
nada: se consulta el relevo, que atiende la petición con una página de navegador (ver
``PoTokenMinter``). Solo responden los clientes web; ios y android nunca llegan hasta aquí, así que
su camino rápido no espera. Cuando falta el token, la petición espera lo que tarde el navegador: un
segundo si ya está caliente y más si arranca, porque yt-dlp liga el siguiente intento a otro binding
y un token pedido y no recogido no le serviría.
"""

import threading
import time
from typing import Optional

from yt_dlp.extractor.youtube.pot.provider import (
    PoTokenContext,
    PoTokenProvider,
    PoTokenProviderError,
    PoTokenProviderRejectedRequest,
    PoTokenRequest,
    PoTokenResponse,
    register_provider,
)
from yt_dlp.extractor.youtube.pot.utils import WEBPO_CLIENTS, get_webpo_content_binding

from backend.interfaces import IPoTokenSource

WARM_WAIT_SECONDS = 2.0
COLD_WAIT_SECONDS = 15.0
POLL_SECONDS = 0.1
TOKEN_TTL_SECONDS = 3600


class MiniKickPTP(PoTokenProvider):
    PROVIDER_VERSION = "1.0.0"
    BUG_REPORT_LOCATION = "https://github.com/Andro2k/MiniKick/issues"
    _SUPPORTED_CONTEXTS = (PoTokenContext.GVS, PoTokenContext.PLAYER)
    _SUPPORTED_CLIENTS = WEBPO_CLIENTS
    _SUPPORTED_EXTERNAL_REQUEST_FEATURES = None

    _source: Optional[IPoTokenSource] = None

    def is_available(self) -> bool:
        return self._source is not None

    def _real_request_pot(self, request: PoTokenRequest) -> PoTokenResponse:
        binding, _kind = get_webpo_content_binding(request)
        if not binding:
            raise PoTokenProviderRejectedRequest("this request has no content binding")

        source = self._source
        token = source.token(binding)
        if token is None:
            token = self._wait_for(source, binding)
        if token is None:
            raise PoTokenProviderError("the PO token is not ready yet", expected=True)
        return PoTokenResponse(po_token=token, expires_at=int(time.time()) + TOKEN_TTL_SECONDS)

    def _wait_for(self, source: IPoTokenSource, binding: str) -> Optional[str]:
        deadline = time.monotonic() + (WARM_WAIT_SECONDS if source.warm() else COLD_WAIT_SECONDS)
        while time.monotonic() < deadline:
            time.sleep(POLL_SECONDS)
            token = source.minted(binding)
            if token is not None:
                return token
        return None


_register_lock = threading.Lock()
_registered = False


def register_po_token_provider(source: IPoTokenSource) -> None:
    """Deja ``source`` como origen de tokens y registra el proveedor en yt-dlp una sola vez por proceso."""
    global _registered
    with _register_lock:
        MiniKickPTP._source = source
        if not _registered:
            register_provider(MiniKickPTP)
            _registered = True
