# frontend\window\po_token_coordinator.py
"""Lado Qt del generador de PO tokens: una página de QtWebEngine oculta y el temporizador que la atiende."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote

from PySide6.QtCore import QObject, QTimer, QUrl

from backend.interfaces import IPoTokenMintQueue, IPoTokenPage, PoTokenAnswer
from backend.services.music.po_token_minter_service import IDLE_TICK_SECONDS, PoTokenMinter
from backend.utils import fast_dumps, fast_loads

logger = logging.getLogger(__name__)

# El reproductor incrustado del primer video de YouTube: una página mínima que carga el cliente de BotGuard.
_PAGE_URL = "https://www.youtube.com/embed/jNQXAC9IVRw"
_RESULT_KEY = "__mkPoToken"
_ASK_FUNCTION = "mkPoToken"

# Corre al crear cada documento, en el mundo principal, para ver los objetos que define la propia página.
# Busca el cliente que la página de YouTube trae para atestiguar y le pide un token por ``binding``.
# La página reescribe su URL y navega mientras carga, así que el binding pendiente se guarda en sessionStorage.
_SCRIPT = r"""
(function () {
  "use strict";
  var RESULT = "__mkPoToken", ASK = "mkPoToken", STORE = "mk-po-binding";
  var PATIENCE_MS = 30000, STEP_MS = 200;
  var state = { binding: null, token: null, error: null };
  var run = 0;

  function findMinter() {
    var names;
    try { names = Object.getOwnPropertyNames(window); } catch (e) { return null; }
    for (var i = 0; i < names.length; i++) {
      var holder;
      try { holder = window[names[i]]; } catch (e) { continue; }
      if (!holder || (typeof holder !== "object" && typeof holder !== "function") || holder === window) continue;
      try {
        if (typeof holder.wpc === "function") return holder.wpc;
        var keys = Object.keys(holder);
        for (var k = 0; k < keys.length; k++) {
          var inner = holder[keys[k]];
          if (inner && typeof inner.wpc === "function") return inner.wpc.bind(inner);
        }
      } catch (e) { /* una propiedad con acceso prohibido no es el cliente */ }
    }
    return null;
  }

  function mint(binding) {
    var mine = ++run, started = Date.now();
    state = { binding: binding, token: null, error: null };
    try { sessionStorage.setItem(STORE, binding); } catch (e) { /* sin almacenamiento, sigue sin sobrevivir a navegar */ }

    function fail(reason) { if (mine === run) state = { binding: binding, token: null, error: String(reason) }; }

    function attempt() {
      if (mine !== run) return;
      if (Date.now() - started > PATIENCE_MS) return fail("timeout");
      var wpc = findMinter();
      if (!wpc) return setTimeout(attempt, STEP_MS);
      Promise.resolve(wpc()).then(function (client) {
        if (!client || typeof client.mws !== "function") return setTimeout(attempt, STEP_MS);
        return Promise.resolve(client.mws({ c: binding, mc: false, me: false })).then(function (token) {
          if (mine !== run) return;
          if (typeof token === "string" && token) state = { binding: binding, token: token, error: null };
          else setTimeout(attempt, STEP_MS);
        });
      }).catch(function () {
        // El atestiguado aún no está listo: se reintenta hasta agotar la paciencia.
        setTimeout(attempt, STEP_MS);
      });
    }
    attempt();
  }

  Object.defineProperty(window, RESULT, { get: function () { return JSON.stringify(state); }, configurable: true });
  Object.defineProperty(window, ASK, { value: mint, configurable: true });

  var pending = null;
  try { pending = new URLSearchParams(location.search).get("binding"); } catch (e) { /* sin binding en la URL */ }
  if (!pending) { try { pending = sessionStorage.getItem(STORE); } catch (e) { /* sin binding guardado */ } }
  if (pending) mint(pending);
})();
"""


class WebEnginePoTokenPage:
    """Implementa ``IPoTokenPage`` con una página de QtWebEngine sin vista, silenciada y sin perfil persistente."""

    def __init__(self, binding: str):
        from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineScript, QWebEnginePage

        self._profile = QWebEngineProfile()
        self._page = QWebEnginePage(self._profile)
        self._page.setAudioMuted(True)
        self._page.setLifecycleState(QWebEnginePage.LifecycleState.Active)
        self._page.renderProcessTerminated.connect(self._on_render_terminated)

        script = QWebEngineScript()
        script.setName("mk-po-token")
        script.setSourceCode(_SCRIPT)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        self._page.scripts().insert(script)

        self._binding = binding
        self._latest: Optional[PoTokenAnswer] = None
        self._error: Optional[str] = None
        self._page.load(QUrl(f"{_PAGE_URL}?binding={quote(binding, safe='')}"))

    def ask(self, binding: str) -> None:
        self._binding = binding
        self._latest = None
        self._page.runJavaScript(f"window.{_ASK_FUNCTION} && window.{_ASK_FUNCTION}({fast_dumps(binding)})")

    def answer(self) -> Optional[PoTokenAnswer]:
        """La última respuesta conocida; además pide a la página la siguiente."""
        if self._error is not None:
            return PoTokenAnswer(self._binding, error=self._error)
        self._page.runJavaScript(f"window.{_RESULT_KEY}", self._on_result)
        return self._latest

    def close(self) -> None:
        self._page.deleteLater()
        self._profile.deleteLater()

    def _on_result(self, raw) -> None:
        if not isinstance(raw, str):
            return
        try:
            state = fast_loads(raw)
        except ValueError:
            return
        if state.get("binding") != self._binding:
            return
        if state.get("token") or state.get("error"):
            self._latest = PoTokenAnswer(state["binding"], state.get("token"), state.get("error"))

    def _on_render_terminated(self, status, exit_code) -> None:
        self._error = f"render process terminated ({status}, {exit_code})"


def open_web_engine_page(binding: str) -> IPoTokenPage:
    return WebEnginePoTokenPage(binding)


class PoTokenCoordinator(QObject):
    """Llama a ``PoTokenMinter.tick()`` con el ritmo que la propia máquina de estados pide."""

    def __init__(self, queue: IPoTokenMintQueue, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._minter = PoTokenMinter(queue, open_web_engine_page)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_tick)

    def start(self) -> None:
        self._timer.start(int(IDLE_TICK_SECONDS * 1000))

    def shutdown(self) -> None:
        self._timer.stop()
        self._minter.close()

    def _on_tick(self) -> None:
        try:
            delay = self._minter.tick()
        except Exception:
            logger.exception("[PoToken] Minting tick failed")
            delay = IDLE_TICK_SECONDS
        self._timer.start(int(delay * 1000))
