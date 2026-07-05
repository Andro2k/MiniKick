# backend\services\system\dashboard_service.py

import logging
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

class AvatarService(QObject):
    avatar_downloaded = Signal(bytes)

    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self._on_finished)

    def _get_cached_avatar(self, url: str) -> bytes | None:
        if not self.db_manager:
            return None
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT image_bytes FROM avatar_cache WHERE url = ?", (url.strip(),))
                r = cursor.fetchone()
                if r:
                    return r[0]
        except Exception as e:
            logging.error("[AvatarService] Error reading from cache: %s", e)
        return None

    def _save_avatar_to_cache(self, url: str, data: bytes):
        if not self.db_manager:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO avatar_cache (url, image_bytes) VALUES (?, ?)
                    ON CONFLICT(url) DO UPDATE SET image_bytes=excluded.image_bytes, cached_at=CURRENT_TIMESTAMP
                """, (url.strip(), data))
                conn.commit()
        except Exception as e:
            logging.error("[AvatarService] Error saving to cache: %s", e)

    def fetch_avatar(self, url_str: str):
        if not url_str:
            return
        
        cached = self._get_cached_avatar(url_str)
        if cached:
            self.avatar_downloaded.emit(cached)
            return

        request = QNetworkRequest(QUrl(url_str))
        self.manager.get(request)

    def _on_finished(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            url_str = reply.url().toString()
            data = reply.readAll().data()
            self._save_avatar_to_cache(url_str, data)
            self.avatar_downloaded.emit(data)
        reply.deleteLater()