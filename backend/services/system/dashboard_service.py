# backend\services\system\dashboard_service.py

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from backend.database.avatar_storage import SQLiteAvatarStorage

class AvatarService(QObject):
    avatar_downloaded = Signal(bytes)
    avatar_ready = Signal(str, bytes)

    def __init__(self, avatar_storage: SQLiteAvatarStorage = None, db_manager=None):
        super().__init__()
        if avatar_storage:
            self.storage = avatar_storage
        elif db_manager:
            self.storage = SQLiteAvatarStorage(db_manager)
        else:
            self.storage = None
        self._pending_tags = {}
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self._on_finished)

    def _get_cached_avatar(self, url: str) -> bytes | None:
        if not self.storage:
            return None
        return self.storage.get_cached(url)

    def _save_avatar_to_cache(self, url: str, data: bytes):
        if not self.storage:
            return
        self.storage.save_to_cache(url, data)

    def fetch_avatar(self, url_str: str, tag: str = ""):
        if not url_str:
            return
        
        cached = self._get_cached_avatar(url_str)
        if cached:
            self.avatar_downloaded.emit(cached)
            self.avatar_ready.emit(tag or url_str, cached)
            return

        if tag:
            self._pending_tags[url_str] = tag
        request = QNetworkRequest(QUrl(url_str))
        self.manager.get(request)

    def _on_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            url_str = reply.url().toString()
            data = reply.readAll().data()
            self._save_avatar_to_cache(url_str, data)
            tag = self._pending_tags.pop(url_str, "")
            self.avatar_downloaded.emit(data)
            self.avatar_ready.emit(tag or url_str, data)
        reply.deleteLater()
