# backend/services/dashboard_service.py

from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class AvatarService(QObject):
    avatar_downloaded = Signal(bytes)

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self._on_finished)

    def fetch_avatar(self, url_str: str):
        if not url_str:
            return
        request = QNetworkRequest(QUrl(url_str))
        self.manager.get(request)

    def _on_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll().data()
            self.avatar_downloaded.emit(data)
        reply.deleteLater()