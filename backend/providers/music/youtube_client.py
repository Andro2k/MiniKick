# backend\providers\music\youtube_client.py

import logging
import os
from PySide6.QtCore import QObject, QUrl, QTimer, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from backend.workers.music_worker import YouTubeResolveWorker, YouTubeSearchWorker

_ERR_INVALID_MEDIA = "INVALID_MEDIA"
_ERR_PLAYER_ERROR = "PLAYER_ERROR"

class YouTubeMusicProvider(QObject):
    resolve_error_occurred = Signal(str, str, str)

    def __init__(self, i18n, db_manager=None):
        super().__init__()
        self.i18n = i18n
        self.db_manager = db_manager
        self.queue: list[dict] = []
        self.current_song: dict | None = None
        self.current_local_file: str | None = None
        self.resolve_worker = None
        self._search_workers = []

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self.player.mediaStatusChanged.connect(self._handle_media_status)
        self.player.errorOccurred.connect(self._handle_player_error)

        self.auto_resume = True
        self._start_playing_current = True
        if self.db_manager:
            try:
                from backend.database import SQLiteSettingsStorage
                settings = SQLiteSettingsStorage(self.db_manager)
                self.auto_resume = settings.load_bool("youtube_auto_resume", True)
            except Exception as e:
                logging.error("[YouTubeMusicProvider] Error loading auto_resume setting: %s", e)

        if self.db_manager:
            pending = self.db_manager.load_pending_songs("youtube")
            for song in pending:
                self.queue.append({
                    "db_id": song["db_id"],
                    "title": song["title"],
                    "artist": song["artist"],
                    "url": song["url"],
                    "resolved": False,
                    "stream_url": None,
                    "requester": song["requester"]
                })
            
            if self.queue:
                from PySide6.QtCore import QTimer
                if self.auto_resume:
                    QTimer.singleShot(0, lambda: self._play_next(start_playing=True))
                else:
                    QTimer.singleShot(0, lambda: self._play_next(start_playing=False))

    def _get_cached_search(self, query: str) -> dict | None:
        if not self.db_manager:
            return None
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT title, artist, url FROM youtube_search_cache WHERE LOWER(query_raw) = ?", (query.lower().strip(),))
                r = cursor.fetchone()
                if r:
                    return {"title": r[0], "artist": r[1], "url": r[2]}
        except Exception as e:
            logging.error("[YouTubeMusicProvider] Error reading from search cache: %s", e)
        return None

    def _save_search_to_cache(self, query: str, song_entry: dict):
        if not self.db_manager:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO youtube_search_cache (query_raw, title, artist, url) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(query_raw) DO UPDATE SET 
                        title=excluded.title, artist=excluded.artist, url=excluded.url, cached_at=CURRENT_TIMESTAMP
                """, (query.lower().strip(), song_entry["title"], song_entry["artist"], song_entry["url"]))
                conn.commit()
        except Exception as e:
            logging.error("[YouTubeMusicProvider] Error saving to search cache: %s", e)

    def get_current_song(self) -> dict | None:
        if not self.current_song:
            return None

        is_resolving = (self.resolve_worker is not None and self.resolve_worker.isRunning())
        is_playing = is_resolving or (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        return {
            "title": self.current_song["title"],
            "artist": self.current_song["artist"],
            "url": self.current_song["url"],
            "is_playing": is_playing
        }

    @property
    def provider_id(self) -> str:
        return "youtube"

    def add_to_queue(self, query_or_uri: str, callback=None, requester: str = None) -> tuple[bool, str]:
        query = query_or_uri.strip()
        is_search = not (query.startswith("http://") or query.startswith("https://") or query.startswith("www."))
        
        if is_search:
            cached = self._get_cached_search(query)
            if cached:
                song_entry = {
                    "title": cached["title"],
                    "artist": cached["artist"],
                    "url": cached["url"],
                    "resolved": False,
                    "stream_url": None,
                    "requester": requester
                }
                if self.db_manager:
                    db_id = self.db_manager.add_song_to_queue(
                        title=song_entry["title"],
                        artist=song_entry["artist"],
                        url=song_entry["url"],
                        requester=requester,
                        provider="youtube"
                    )
                    song_entry["db_id"] = db_id
                self.queue.append(song_entry)
                if not self.current_song:
                    if self.auto_resume:
                        QTimer.singleShot(0, lambda: self._play_next(start_playing=True))
                    else:
                        QTimer.singleShot(0, lambda: self._play_next(start_playing=False))
                
                success_msg = self.i18n.get("music.queue.success").replace("{track}", f"{cached['title']} - {cached['artist']}")
                return True, success_msg

            search_query = f"ytsearch1:{query}"
            immediate_msg = self.i18n.get("music.queue.searching").replace("{query}", query)
        else:
            search_query = query
            immediate_msg = self.i18n.get("music.queue.processing_link")

        worker = YouTubeSearchWorker(search_query, query, self.i18n)
        
        def on_worker_finished(success, message):
            if success and worker.song_entry:
                worker.song_entry["requester"] = requester
                if self.db_manager:
                    db_id = self.db_manager.add_song_to_queue(
                        title=worker.song_entry["title"],
                        artist=worker.song_entry["artist"],
                        url=worker.song_entry["url"],
                        requester=requester,
                        provider="youtube"
                    )
                    worker.song_entry["db_id"] = db_id
                self.queue.append(worker.song_entry)
                if is_search:
                    self._save_search_to_cache(query, worker.song_entry)
                if not self.current_song:
                    self._play_next(start_playing=self.auto_resume)
            if callback:
                callback(success, message)
            
            if worker in self._search_workers:
                self._search_workers.remove(worker)
            worker.deleteLater()

        worker.finished.connect(on_worker_finished)
        self._search_workers.append(worker)
        worker.start()

        return True, immediate_msg

    def skip_current(self) -> bool:
        self._play_next()
        return True

    def set_volume(self, volume: int) -> None:
        self.audio_output.setVolume(volume / 100.0)

    def get_queue(self) -> list[dict]:
        return list(self.queue)

    def remove_from_queue(self, index: int) -> bool:
        if 0 <= index < len(self.queue):
            song = self.queue.pop(index)
            db_id = song.get("db_id")
            if db_id is not None and self.db_manager:
                self.db_manager.update_song_status(db_id, 2)
            return True
        return False

    def shutdown(self):
        self.player.stop()
        self.player.setSource(QUrl())
        if self.current_local_file and os.path.exists(self.current_local_file):
            try:
                os.remove(self.current_local_file)
            except Exception:
                pass
        self.current_local_file = None

    def _play_next(self, start_playing: bool = True):
        if self.resolve_worker and self.resolve_worker.isRunning():
            self.resolve_worker.terminate()
            self.resolve_worker.wait()

        self.player.stop()
        self.player.setSource(QUrl())

        if self.current_local_file and os.path.exists(self.current_local_file):
            try:
                os.remove(self.current_local_file)
            except Exception as e:
                logging.error("[YouTubeMusicProvider] Error deleting temporary file: %s", e)
        self.current_local_file = None

        if self.current_song:
            db_id = self.current_song.get("db_id")
            if db_id is not None and self.db_manager:
                self.db_manager.update_song_status(db_id, 2)

        if not self.queue:
            self.current_song = None
            return

        self.current_song = self.queue.pop(0)
        
        db_id = self.current_song.get("db_id")
        if db_id is not None and self.db_manager:
            self.db_manager.update_song_status(db_id, 1)

        self.resolve_worker = YouTubeResolveWorker(self.current_song["url"])
        self.resolve_worker.resolved.connect(self._on_song_resolved)
        self.resolve_worker.error.connect(self._on_resolve_error)
        self._start_playing_current = start_playing
        self.resolve_worker.start()

    @Slot(str, str)
    def _on_song_resolved(self, title: str, path_or_url: str):
        if not self.current_song:
            if path_or_url and not (path_or_url.startswith("http://") or path_or_url.startswith("https://")):
                if os.path.exists(path_or_url):
                    try:
                        os.remove(path_or_url)
                    except Exception:
                        pass
            return

        self.current_song["resolved"] = True
        
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            self.current_local_file = None
            self.player.setSource(QUrl(path_or_url))
        else:
            self.current_local_file = path_or_url
            self.player.setSource(QUrl.fromLocalFile(path_or_url))
            
        if self._start_playing_current:
            self.player.play()
        else:
            self.player.pause()

    @Slot(str)
    def _on_resolve_error(self, error_msg: str):
        logging.error("[YouTubeMusicProvider] Error resolving audio stream: %s", error_msg)
        if self.current_song:
            title = self.current_song.get("title", self.i18n.get("music.player.unknown_song"))
            requester = self.current_song.get("requester", "") or ""
            self.resolve_error_occurred.emit(title, error_msg, requester)
        self._play_next()

    @Slot(QMediaPlayer.MediaStatus)
    def _handle_media_status(self, status: QMediaPlayer.MediaStatus):
        if status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            if status == QMediaPlayer.MediaStatus.InvalidMedia and self.current_song:
                title = self.current_song.get("title", self.i18n.get("music.player.unknown_song"))
                requester = self.current_song.get("requester", "") or ""
                self.resolve_error_occurred.emit(title, _ERR_INVALID_MEDIA, requester)
            self._play_next()

    @Slot(QMediaPlayer.Error, str)
    def _handle_player_error(self, error, error_string):
        logging.error("[YouTubeMusicProvider] Player error: %s - %s", error, error_string)
        if self.current_song:
            title = self.current_song.get("title", self.i18n.get("music.player.unknown_song"))
            requester = self.current_song.get("requester", "") or ""
            self.resolve_error_occurred.emit(title, f"{_ERR_PLAYER_ERROR}: {error_string}", requester)
        self._play_next()

    def pause_playback(self) -> bool:
        self.player.pause()
        return True

    def resume_playback(self) -> bool:
        self.player.play()
        return True
