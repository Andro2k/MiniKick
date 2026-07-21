# backend\workers\music_worker.py

import os
import hashlib
from PySide6.QtCore import QThread, Signal
from backend.providers import SpotifyAuthManager

class SpotifyAuthWorker(QThread):
    auth_success = Signal(dict)
    auth_error = Signal(str)

    def __init__(self, i18n, spotify_auth: SpotifyAuthManager, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.spotify_auth = spotify_auth

    def run(self):
        try:
            tokens = self.spotify_auth.storage.load()
            if not tokens or not self.spotify_auth.get_access_token():
                tokens = self.spotify_auth.login()
            
            self.auth_success.emit(tokens)
        except TimeoutError:
            err_msg = self.i18n.get("spotify.error.timeout")
            self.auth_error.emit(err_msg)
        except Exception as e:
            err_prefix = self.i18n.get("spotify.error.generic")
            self.auth_error.emit(f"{err_prefix} {str(e)}")

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
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'socket_timeout': 15,
                'retries': 5,
                'fragment_retries': 5,
                'continuedl': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.query_or_url, download=False)
                if 'entries' in info:
                    info = info['entries'][0]                    
                raw_id = info.get('id', '')
                if len(raw_id) > 64 or '?' in raw_id or '&' in raw_id or '=' in raw_id or '/' in raw_id or '\\' in raw_id:
                    info['id'] = hashlib.md5(self.query_or_url.encode('utf-8')).hexdigest()
                
                try:
                    ydl.process_info(info)
                    local_path = ydl.prepare_filename(info)
                except Exception as download_err:
                    local_path = ydl.prepare_filename(info)
                    part_file = local_path + ".part"
                    if os.path.exists(part_file):
                        try:
                            os.remove(part_file)
                        except Exception:
                            pass
                    if os.path.exists(local_path):
                        try:
                            os.remove(local_path)
                        except Exception:
                            pass
                    
                    stream_url = info.get('url')
                    if stream_url:
                        title = info.get('title', 'Unknown Title')
                        self.resolved.emit(title, stream_url)
                        return
                    else:
                        raise download_err
                
                title = info.get('title', 'Unknown Title')
                if os.path.exists(local_path):
                    self.resolved.emit(title, local_path)
                else:
                    stream_url = info.get('url')
                    if stream_url:
                        self.resolved.emit(title, stream_url)
                    else:
                        raise Exception("Stream URL not found in metadata")
            
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
                'nocheckcertificate': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
                'socket_timeout': 15,
                'retries': 5,
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

                title = item.get('title', self.i18n.get("music.player.unknown_song"))
                video_id = item.get('id')
                is_youtube = False
                ie_key = item.get('ie_key')
                if ie_key and ie_key.lower() == 'youtube':
                    is_youtube = True
                elif 'youtube' in item.get('extractor', '').lower() or 'youtube' in info.get('extractor', '').lower():
                    is_youtube = True
                elif video_id and len(video_id) == 11:
                    is_youtube = True
                
                if is_youtube and video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    video_url = item.get('webpage_url') or item.get('url')
                
                if video_url and not video_url.startswith("http"):
                    video_url = f"https://www.youtube.com/watch?v={video_url}"
                elif not video_url:
                    if video_id:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        msg = self.i18n.get("music.queue.no_link")
                        self.finished.emit(False, msg)
                        return

                author = item.get('uploader') or item.get('channel', '-')

                duration_sec = item.get('duration')
                duration_str = "-"
                if duration_sec:
                    try:
                        m, s = divmod(int(duration_sec), 60)
                        duration_str = f"{m:02d}:{s:02d}"
                    except Exception:
                        pass
                elif item.get('duration_string'):
                    duration_str = item.get('duration_string')

                self.song_entry = {
                    "title": title,
                    "artist": author,
                    "url": video_url,
                    "resolved": False,
                    "stream_url": None,
                    "duration": duration_str,
                    "thumbnail": item.get('thumbnail') or info.get('thumbnail') or ""
                }

                msg = self.i18n.get("music.queue.success").replace("{track}", f"{title} - {author}")
                self.finished.emit(True, msg)

        except Exception as e:
            msg = self.i18n.get("music.queue.error").replace("{error}", str(e))
            self.finished.emit(False, msg)
