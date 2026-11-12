# frontend\components\music\video_preview_panel.py

import logging
import time
from string import Template

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from backend.utils.youtube_url import youtube_video_id
from frontend.common import Palette, Size

logger = logging.getLogger("minikick.music.video_preview")

_EMBED_HOST = "https://www.youtube-nocookie.com"
_ERROR_TITLE_PREFIX = "mk-yt-error:"
_READY_TITLE = "mk-yt-ready"
_LOAD_TIMEOUT_MS = 8000
HIDE_GRACE_MS = 300
_MAX_LOAD_RETRIES = 1
_MIN_VIDEO_HEIGHT = 320
_PLAYER_HTML = Template("""<!DOCTYPE html><html><head><meta charset="utf-8"><title>-</title>
<style>html,body,#player{margin:0;width:100%;height:100%;overflow:hidden;background:$background}</style></head>
<body><div id="player"></div>
<script>
function fail(code){document.title='$prefix'+code;}
function onYouTubeIframeAPIReady(){
  new YT.Player('player',{host:'$host',width:'100%',height:'100%',videoId:'$video_id',
    playerVars:{autoplay:1,mute:1,playsinline:1,rel:0},
    events:{onReady:function(){document.title='$ready';},onError:function(e){fail(e.data);}}});
}
</script>
<script src="https://www.youtube.com/iframe_api" onerror="fail('load')"></script>
</body></html>""")


class _ClickableVideoWidget(QVideoWidget):
    clicked = Signal()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class MusicVideoPreviewPanel(QWidget):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._source_url = ""
        self._view = None
        self._local_player = None
        self._local_widget = None
        self._attempt = 0
        self._load_started = 0.0
        self._load_timer = QTimer(self)
        self._load_timer.setSingleShot(True)
        self._load_timer.setInterval(_LOAD_TIMEOUT_MS)
        self._load_timer.timeout.connect(self._on_load_timeout)
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

    def load(self, url: str, local_path: str | None = None):
        self._source_url = url or ""
        video_id = youtube_video_id(self._source_url)
        if video_id is None:
            self._show_error()
            return
        self._attempt = 0
        if local_path:
            self._drop_view()
            self._start_local(local_path)
        else:
            self._stop_local()
            self._start_load(video_id)

    def _start_local(self, path: str):
        self._ensure_local()
        self._error_box.hide()
        self._video_host.show()
        self._local_widget.show()
        logger.info("[MusicVideo] Playing cached file %s", path)
        self._local_player.setSource(QUrl.fromLocalFile(path))
        self._local_player.play()

    def _ensure_local(self):
        if self._local_player is None:
            self._local_widget = _ClickableVideoWidget(self._video_host)
            self._video_host.layout().addWidget(self._local_widget)
            self._local_player = QMediaPlayer(self)
            self._local_player.setVideoOutput(self._local_widget)
            self._local_player.setLoops(QMediaPlayer.Loops.Infinite)
            self._local_player.mediaStatusChanged.connect(self._on_local_status)
            self._local_player.errorOccurred.connect(self._on_local_error)
            self._local_widget.clicked.connect(self._toggle_local_playback)

    def _stop_local(self):
        if self._local_player is not None:
            self._local_player.stop()
            self._local_player.setSource(QUrl())
            self._local_widget.hide()

    def _toggle_local_playback(self):
        if self._local_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._local_player.pause()
        else:
            self._local_player.play()

    def _on_local_status(self, status):
        loaded = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)
        if status in loaded and not self._local_player.hasVideo():
            self._fallback_to_embed("the cached file has no video track")

    def _on_local_error(self, _error, message: str):
        self._fallback_to_embed(message)

    def _fallback_to_embed(self, reason: str):
        if self._local_player is None or self._local_player.source().isEmpty():
            return
        logger.info("[MusicVideo] Cached playback unavailable (%s); using the YouTube embed", reason)
        self._stop_local()
        video_id = youtube_video_id(self._source_url)
        if video_id:
            self._start_load(video_id)

    def _start_load(self, video_id: str):
        self._error_box.hide()
        self._video_host.show()
        html = _PLAYER_HTML.substitute(
            background=Palette.NEUTRAL_900, prefix=_ERROR_TITLE_PREFIX, ready=_READY_TITLE, host=_EMBED_HOST, video_id=video_id,
        )
        self._load_started = time.monotonic()
        logger.info("[MusicVideo] Loading %s (attempt %d)", video_id, self._attempt + 1)
        self._ensure_view().setHtml(html, QUrl(f"{_EMBED_HOST}/"))
        self._load_timer.start()

    def _on_load_timeout(self):
        video_id = youtube_video_id(self._source_url)
        if self._attempt < _MAX_LOAD_RETRIES and video_id:
            self._attempt += 1
            logger.warning("[MusicVideo] Player not ready after %d ms, retrying with a fresh view", _LOAD_TIMEOUT_MS)
            self.unload()
            self._start_load(video_id)
            return
        logger.warning("[MusicVideo] Player never became ready for %s", self._source_url)
        self._show_error()

    def unload(self):
        self._load_timer.stop()
        self._stop_local()
        self._drop_view()

    def _drop_view(self):
        if self._view is None:
            return
        view, self._view = self._view, None
        view.titleChanged.disconnect(self._on_title_changed)
        view.setUrl(QUrl("about:blank"))
        view.hide()
        view.deleteLater()

    def hideEvent(self, event):
        super().hideEvent(event)
        QTimer.singleShot(HIDE_GRACE_MS, self._unload_if_hidden)

    def _unload_if_hidden(self):
        if not self.isVisible():
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
        if title == _READY_TITLE:
            self._load_timer.stop()
            logger.info("[MusicVideo] Player ready in %d ms", (time.monotonic() - self._load_started) * 1000)
        elif title.startswith(_ERROR_TITLE_PREFIX):
            logger.info("[MusicVideo] Embed failed (code %s) for %s", title[len(_ERROR_TITLE_PREFIX):], self._source_url)
            self._show_error()

    def _show_error(self):
        self.unload()
        self._video_host.hide()
        self._error_box.show()

    def _open_in_browser(self):
        if self._source_url:
            QDesktopServices.openUrl(QUrl(self._source_url))
