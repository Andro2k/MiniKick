# frontend\\components\\music\\video_preview_panel.py

import logging
from string import Template

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from backend.utils.youtube_url import youtube_video_id
from frontend.common import Palette, Size

logger = logging.getLogger("minikick.music.video_preview")

_EMBED_HOST = "https://www.youtube-nocookie.com"
_ERROR_TITLE_PREFIX = "mk-yt-error:"
_MIN_VIDEO_HEIGHT = 240
_PLAYER_HTML = Template("""<!DOCTYPE html><html><head><meta charset="utf-8"><title>-</title>
<style>html,body,#player{margin:0;width:100%;height:100%;overflow:hidden;background:$background}</style></head>
<body><div id="player"></div>
<script>
function fail(code){document.title='$prefix'+code;}
function onYouTubeIframeAPIReady(){
  new YT.Player('player',{host:'$host',width:'100%',height:'100%',videoId:'$video_id',
    playerVars:{autoplay:1,mute:1,playsinline:1,rel:0},
    events:{onError:function(e){fail(e.data);}}});
}
</script>
<script src="https://www.youtube.com/iframe_api" onerror="fail('load')"></script>
</body></html>""")


class MusicVideoPreviewPanel(QWidget):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._source_url = ""
        self._view = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*Size.Margin.MRG_NON)
        layout.setSpacing(Size.SPACING_NN)

        self._video_host = QWidget(self)
        self._video_host.setMinimumHeight(_MIN_VIDEO_HEIGHT)
        host_layout = QVBoxLayout(self._video_host)
        host_layout.setContentsMargins(*Size.Margin.MRG_NON)
        layout.addWidget(self._video_host)

        self._error_box = QWidget(self)
        self._error_box.setMinimumHeight(_MIN_VIDEO_HEIGHT)
        error_layout = QVBoxLayout(self._error_box)
        error_layout.setContentsMargins(*Size.Margin.MRG_NON)
        error_layout.setSpacing(Size.SPACING_MD)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_error = QLabel(self.i18n.get("music.queue.preview_error"), self._error_box)
        self.lbl_error.setProperty("role", "body")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_layout.addWidget(self.lbl_error)

        self.btn_open_browser = QPushButton(self.i18n.get("music.queue.preview_open_browser"), self._error_box)
        self.btn_open_browser.setProperty("role", "action_outlined")
        self.btn_open_browser.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_browser.clicked.connect(self._open_in_browser)
        error_layout.addWidget(self.btn_open_browser, alignment=Qt.AlignmentFlag.AlignCenter)

        self._error_box.hide()
        layout.addWidget(self._error_box)

    def load(self, url: str):
        self._source_url = url or ""
        video_id = youtube_video_id(self._source_url)
        if video_id is None:
            self._show_error()
            return
        self._error_box.hide()
        self._video_host.show()
        html = _PLAYER_HTML.substitute(
            background=Palette.NEUTRAL_900, prefix=_ERROR_TITLE_PREFIX, host=_EMBED_HOST, video_id=video_id,
        )
        self._ensure_view().setHtml(html, QUrl(f"{_EMBED_HOST}/"))

    def unload(self):
        if self._view is None:
            return
        view, self._view = self._view, None
        view.titleChanged.disconnect(self._on_title_changed)
        view.setUrl(QUrl("about:blank"))
        view.hide()
        view.deleteLater()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.unload()

    def _ensure_view(self):
        if self._view is None:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

            view = QWebEngineView(self._video_host)
            view.page().setBackgroundColor(QColor(Palette.NEUTRAL_900))
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
            view.titleChanged.connect(self._on_title_changed)
            self._video_host.layout().addWidget(view)
            self._view = view
        return self._view

    def _on_title_changed(self, title: str):
        if title.startswith(_ERROR_TITLE_PREFIX):
            logger.info("[MusicVideo] Embed failed (code %s) for %s", title[len(_ERROR_TITLE_PREFIX):], self._source_url)
            self._show_error()

    def _show_error(self):
        self.unload()
        self._video_host.hide()
        self._error_box.show()

    def _open_in_browser(self):
        if self._source_url:
            QDesktopServices.openUrl(QUrl(self._source_url))
