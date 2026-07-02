# backend\providers\youtube\youtube_client.py

import os
from PySide6.QtCore import QObject, QUrl, QThread, Signal, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from abc import ABCMeta
from backend.interfaces.music_interfaces import MusicPlayerProvider

class YouTubeResolveWorker(QThread):
    resolved = Signal(str, str)
    error = Signal(str)

    def __init__(self, query_or_url: str):
        super().__init__()
        self.query_or_url = query_or_url

    def run(self):
        try:
            import yt_dlp
            
            app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            cache_dir = os.path.join(app_data_dir, '.Minikick', 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            
            outtmpl = os.path.join(cache_dir, 'yt_%(id)s.%(ext)s')
            
            ydl_opts_download = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                    info = ydl.extract_info(self.query_or_url, download=True)
                    if 'entries' in info:
                        info = info['entries'][0]
                    local_path = ydl.prepare_filename(info)
                    title = info.get('title', 'Unknown Title')
                    
                    if os.path.exists(local_path):
                        self.resolved.emit(title, local_path)
                        return
            except Exception as download_err:
                print(f"[YouTubeResolveWorker] El intento de descarga local falló: {download_err}. Usando fallback de streaming remoto.")
            
            ydl_opts_stream = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts_stream) as ydl:
                info = ydl.extract_info(self.query_or_url, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                stream_url = info['url']
                title = info.get('title', 'Unknown Title')
                self.resolved.emit(title, stream_url)
            
        except Exception as e:
            self.error.emit(str(e))


class YouTubeSearchWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, search_query: str, query_raw: str, i18n):
        super().__init__()
        self.search_query = search_query
        self.query_raw = query_raw
        self.i18n = i18n
        self.song_entry = None

    def run(self):
        try:
            import yt_dlp
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.search_query, download=False)
                if not info:
                    msg = self.i18n.get("music.queue.not_found").replace("{query}", self.query_raw)
                    self.finished.emit(False, msg)
                    return

                if 'entries' in info:
                    entries = list(info['entries'])
                    if not entries:
                        msg = self.i18n.get("music.queue.not_found").replace("{query}", self.query_raw)
                        self.finished.emit(False, msg)
                        return
                    item = entries[0]
                else:
                    item = info

                title = item.get('title', 'Unknown Title')
                video_url = item.get('url') or item.get('webpage_url')
                
                if video_url and not video_url.startswith("http"):
                    video_url = f"https://www.youtube.com/watch?v={video_url}"
                elif not video_url:
                    video_id = item.get('id')
                    if video_id:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        self.finished.emit(False, "No se pudo obtener el enlace del video")
                        return

                author = item.get('uploader') or item.get('channel', '-')

                self.song_entry = {
                    "title": title,
                    "artist": author,
                    "url": video_url,
                    "resolved": False,
                    "stream_url": None
                }

                msg = self.i18n.get("music.queue.success").replace("{track}", f"{title} - {author}")
                self.finished.emit(True, msg)

        except Exception as e:
            msg = self.i18n.get("music.queue.error").replace("{error}", str(e))
            self.finished.emit(False, msg)


class YouTubeMusicProviderMeta(type(QObject), ABCMeta):
    pass


class YouTubeMusicProvider(QObject, MusicPlayerProvider, metaclass=YouTubeMusicProviderMeta):
    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
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

    def get_current_song(self) -> dict | None:
        if not self.current_song:
            return None

        is_playing = (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        return {
            "title": self.current_song["title"],
            "artist": self.current_song["artist"],
            "url": self.current_song["url"],
            "is_playing": is_playing
        }

    def add_to_queue(self, query_or_uri: str, callback=None) -> tuple[bool, str]:
        query = query_or_uri.strip()
        if not (query.startswith("http://") or query.startswith("https://") or query.startswith("www.")):
            search_query = f"ytsearch1:{query}"
            immediate_msg = f"🔍 Buscando \"{query}\" en YouTube..."
        else:
            search_query = query
            immediate_msg = f"🔍 Procesando enlace de YouTube..."

        worker = YouTubeSearchWorker(search_query, query, self.i18n)
        
        def on_worker_finished(success, message):
            if success and worker.song_entry:
                self.queue.append(worker.song_entry)
                if not self.current_song:
                    self._play_next()
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

    def shutdown(self):
        self.player.stop()
        self.player.setSource(QUrl())
        if self.current_local_file and os.path.exists(self.current_local_file):
            try:
                os.remove(self.current_local_file)
            except Exception:
                pass
        self.current_local_file = None

    def _play_next(self):
        if self.resolve_worker and self.resolve_worker.isRunning():
            self.resolve_worker.terminate()
            self.resolve_worker.wait()

        self.player.stop()
        self.player.setSource(QUrl())

        if self.current_local_file and os.path.exists(self.current_local_file):
            try:
                os.remove(self.current_local_file)
            except Exception as e:
                print(f"[YouTubeMusicProvider] Error eliminando archivo temporal: {e}")
        self.current_local_file = None

        if not self.queue:
            self.current_song = None
            return

        self.current_song = self.queue.pop(0)

        self.resolve_worker = YouTubeResolveWorker(self.current_song["url"])
        self.resolve_worker.resolved.connect(self._on_song_resolved)
        self.resolve_worker.error.connect(self._on_resolve_error)
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
            
        self.player.play()

    @Slot(str)
    def _on_resolve_error(self, error_msg: str):
        print(f"[YouTubeMusicProvider] Error resolviendo stream de audio: {error_msg}")
        self._play_next()

    @Slot(QMediaPlayer.MediaStatus)
    def _handle_media_status(self, status: QMediaPlayer.MediaStatus):
        if status in (QMediaPlayer.MediaStatus.EndOfMedia, QMediaPlayer.MediaStatus.InvalidMedia):
            self._play_next()
