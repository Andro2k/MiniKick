# backend\workers\music_worker.py

import os
import hashlib
import logging
from PySide6.QtCore import QThread, Signal

def _extract_best_audio_url(info: dict) -> str | None:
    if not info:
        return None
    if info.get('url') and isinstance(info.get('url'), str) and info['url'].startswith('http'):
        return info['url']
    
    formats = info.get('formats') or []
    best_url = None
    best_score = -1
    
    for f in formats:
        url = f.get('url')
        if not url or not isinstance(url, str) or not url.startswith('http'):
            continue
        acodec = str(f.get('acodec', 'none')).lower()
        vcodec = str(f.get('vcodec', 'none')).lower()
        if acodec != 'none':
            is_audio_only = (vcodec == 'none')
            abr = f.get('abr') or f.get('tbr') or 0
            score = abr + (10000 if is_audio_only else 0)
            if score > best_score:
                best_score = score
                best_url = url
    return best_url

def _get_cookie_filepath(app_data_dir: str) -> str | None:
    for filename in ('cookies.txt', 'youtube_cookies.txt'):
        cookie_path = os.path.join(app_data_dir, '.Minikick', filename)
        if os.path.isfile(cookie_path) and os.path.getsize(cookie_path) > 0:
            return cookie_path
    return None

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
            cookie_file = _get_cookie_filepath(app_data_dir)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'socket_timeout': 10,
                'retries': 2,
                'fragment_retries': 2,
                'continuedl': False,
                'nopart': True,
                'age_limit': 99,
            }
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
            
            info = None
            client_strategies = [
                ['ios', 'android'],
                ['web', 'mweb'],
                ['tv_embedded'],
            ]

            for clients in client_strategies:
                try:
                    attempt_opts = dict(ydl_opts)
                    attempt_opts['extractor_args'] = {'youtube': {'player_client': clients}}
                    with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                        info = ydl.extract_info(self.query_or_url, download=False)
                        if info:
                            ydl_opts = attempt_opts
                            last_err = None
                            break
                except Exception as e:
                    last_err = e
                    logging.debug("[YouTubeResolveWorker] Strategy %s failed: %s", clients, e)
                    continue
            
            if not info:
                if last_err:
                    raise last_err
                raise Exception("Could not extract video metadata")

            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            raw_id = info.get('id', '')
            if len(raw_id) > 64 or any(c in raw_id for c in ('?', '&', '=', '/', '\\')):
                info['id'] = hashlib.md5(self.query_or_url.encode('utf-8')).hexdigest()
            
            title = info.get('title', 'Unknown Title')
            best_stream_url = _extract_best_audio_url(info)

            download_opts = dict(ydl_opts)
            download_opts['format'] = 'bestaudio/best'
            with yt_dlp.YoutubeDL(download_opts) as ydl:
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
                    
                    if best_stream_url:
                        self.resolved.emit(title, best_stream_url)
                        return
                    else:
                        raise download_err
                
                if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                    self.resolved.emit(title, local_path)
                elif best_stream_url:
                    self.resolved.emit(title, best_stream_url)
                else:
                    raise Exception("Stream URL not found in metadata")
            
        except Exception as e:
            self.error.emit(str(e))

class YouTubeSearchWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, search_query: str, query_raw: str, i18n, max_duration_min: int = 10):
        super().__init__()
        self.search_query = search_query
        self.query_raw = query_raw
        self.i18n = i18n
        self.max_duration_min = max_duration_min
        self.song_entry = None

    def run(self):
        try:
            import yt_dlp
            app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            cookie_file = _get_cookie_filepath(app_data_dir)

            base_opts = {
                'extract_flat': True,
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'nocheckcertificate': True,
                'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web', 'mweb']}},
                'socket_timeout': 10,
                'retries': 2,
                'age_limit': 99,
            }
            if cookie_file:
                base_opts['cookiefile'] = cookie_file

            info = None

            try:
                with yt_dlp.YoutubeDL(base_opts) as ydl:
                    res = ydl.extract_info(self.search_query, download=False)
                    if res and res.get('entries') and [e for e in res['entries'] if e]:
                        info = res
            except Exception as e:
                logging.debug("[YouTubeSearchWorker] Search failed: %s", e)

            if not info and self.search_query.startswith("ytsearch1:"):
                raw_term = self.search_query[10:]
                yt_music_url = f"https://music.youtube.com/search?q={raw_term}"
                music_opts = dict(base_opts)
                music_opts['extract_flat'] = 'in_playlist'
                try:
                    with yt_dlp.YoutubeDL(music_opts) as ydl:
                        res = ydl.extract_info(yt_music_url, download=False)
                        if res and res.get('entries') and [e for e in res['entries'] if e]:
                            info = res
                except Exception as e:
                    logging.debug("[YouTubeSearchWorker] YouTube Music search failed: %s", e)

            if not info:
                msg = self.i18n.get("music.queue.not_found").replace("{query}", self.query_raw)
                self.finished.emit(False, msg)
                return

            if 'entries' in info:
                entries = [e for e in info['entries'] if e]
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
            if duration_sec and self.max_duration_min > 0:
                if int(duration_sec) > self.max_duration_min * 60:
                    msg = self.i18n.get("music.chat.song_too_long").replace("{user}", "").replace("{max}", str(self.max_duration_min))
                    self.finished.emit(False, msg)
                    return

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
                "duration_sec": int(duration_sec) if duration_sec else 0,
                "thumbnail": item.get('thumbnail') or info.get('thumbnail') or ""
            }

            msg = self.i18n.get("music.queue.success").replace("{track}", f"{title} - {author}")
            self.finished.emit(True, msg)

        except Exception as e:
            msg = self.i18n.get("music.queue.error").replace("{error}", str(e))
            self.finished.emit(False, msg)

