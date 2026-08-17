# tests\live\chat_benchmark_live.py

import os
import sys
import json
import time
import threading
import argparse
import requests
import websocket
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.providers.chat.kick_websocket import ChatSocketManager
from backend.providers.chat.twitch_websocket import TwitchSocketManager

try:
    from backend.config.api_keys import KICK_PUSHER_CLUSTER, KICK_PUSHER_KEY
    PUSHER_CLUSTER = KICK_PUSHER_CLUSTER
    PUSHER_KEY = KICK_PUSHER_KEY
except ImportError:
    PUSHER_CLUSTER = "us2"
    PUSHER_KEY = "32cbd69e4b950bf97679"

class PlatformBenchmarkStats:
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.lock = threading.Lock()
        self.total_messages = 0
        self.total_bytes = 0
        self.parse_times_ns = []
        self.msg_timestamps = []
        self.errors = 0
        self.connected = False
        self.start_time = None

    def record_message(self, raw_bytes_len: int, parse_time_ns: int):
        now = time.time()
        with self.lock:
            if self.start_time is None:
                self.start_time = now
            self.total_messages += 1
            self.total_bytes += raw_bytes_len
            self.parse_times_ns.append(parse_time_ns)
            self.msg_timestamps.append(now)

    def get_metrics(self) -> dict:
        with self.lock:
            now = time.time()
            duration = (now - self.start_time) if self.start_time else 0.001
            count = self.total_messages
            avg_msg_sec = count / duration if duration > 0 else 0

            recent_5s = [t for t in self.msg_timestamps if (now - t) <= 5.0]
            recent_rate = len(recent_5s) / 5.0

            if self.parse_times_ns:
                avg_latency_us = (sum(self.parse_times_ns) / len(self.parse_times_ns)) / 1000.0
                min_latency_us = min(self.parse_times_ns) / 1000.0
                max_latency_us = max(self.parse_times_ns) / 1000.0
            else:
                avg_latency_us = min_latency_us = max_latency_us = 0.0

            avg_bytes = (self.total_bytes / count) if count > 0 else 0

            return {
                "platform": self.platform_name,
                "total_messages": count,
                "total_bytes": self.total_bytes,
                "avg_bytes_per_msg": avg_bytes,
                "duration_sec": duration,
                "overall_msg_sec": avg_msg_sec,
                "recent_msg_sec": recent_rate,
                "avg_latency_us": avg_latency_us,
                "min_latency_us": min_latency_us,
                "max_latency_us": max_latency_us,
                "errors": self.errors,
                "connected": self.connected
            }

def fetch_kick_room_id(slug: str) -> int:
    url = f"https://kick.com/api/v1/channels/{slug}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    chatroom = data.get("chatroom", {})
    room_id = chatroom.get("id")
    if not room_id:
        raise ValueError(f"No room_id found for Kick channel '{slug}'")
    return room_id

class ChatBenchmarkRunner:
    def __init__(self, kick_channel: str = "xqc", twitch_channel: str = "xqc", duration: int = 0, log_enabled: bool = True):
        self.kick_channel = kick_channel.strip()
        self.twitch_channel = twitch_channel.strip()
        self.duration = duration
        self.log_enabled = log_enabled
        self.kick_stats = PlatformBenchmarkStats("Kick (Pusher WS)")
        self.twitch_stats = PlatformBenchmarkStats("Twitch (IRC WS)")
        self.stop_event = threading.Event()
        self.log_filepath = None
        self.log_file_handle = None

    def _init_logfile(self):
        if not self.log_enabled:
            return
        logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        dt_tag = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_filepath = os.path.join(logs_dir, f"benchmark_{dt_tag}.log")
        self.log_file_handle = open(self.log_filepath, "w", encoding="utf-8")
        self._log(f"📝 Benchmark log started: {os.path.abspath(self.log_filepath)}")

    def _log(self, msg: str):
        print(msg)
        if self.log_file_handle:
            try:
                self.log_file_handle.write(msg + "\n")
                self.log_file_handle.flush()
            except Exception:
                pass

    def run_kick(self, room_id: int):
        socket_mgr = ChatSocketManager(PUSHER_CLUSTER, PUSHER_KEY)
        self.kick_stats.connected = True

        def on_raw_frame_benchmark(ws, raw_data: str):
            if self.stop_event.is_set():
                return
            t0 = time.perf_counter_ns()
            try:
                outer = json.loads(raw_data)
                event = outer.get("event")
                if event == "App\\Events\\ChatMessageEvent":
                    socket_mgr._handle_chat_message(outer, ws)
            except Exception:
                self.kick_stats.errors += 1
            t1 = time.perf_counter_ns()
            self.kick_stats.record_message(len(raw_data.encode('utf-8')), t1 - t0)

        url = f"wss://ws-{PUSHER_CLUSTER}.pusher.com/app/{PUSHER_KEY}?protocol=7&client=js&version=7.6.0"
        socket_mgr.ws = websocket.WebSocketApp(url, on_message=on_raw_frame_benchmark)
        socket_mgr._room_id = room_id
        socket_mgr._running = True

        def on_open_sub(ws):
            socket_mgr._handle_connection_established({}, ws)

        socket_mgr.ws.on_open = on_open_sub

        while not self.stop_event.is_set():
            socket_mgr.ws.run_forever(ping_interval=30, ping_timeout=10)
            if not self.stop_event.is_set():
                time.sleep(2)

    def run_twitch(self):
        socket_mgr = TwitchSocketManager(nick="justinfan12345")
        self.twitch_stats.connected = True

        def on_raw_message_benchmark(ws, raw_data: str):
            if self.stop_event.is_set():
                return
            t0 = time.perf_counter_ns()
            lines = raw_data.split("\r\n")
            for line in lines:
                if not line:
                    continue
                if line.startswith("PING"):
                    ws.send("PONG :tmi.twitch.tv\r\n")
                    continue
                if "PRIVMSG" in line:
                    socket_mgr._parse_privmsg(line)
            t1 = time.perf_counter_ns()
            self.twitch_stats.record_message(len(raw_data.encode('utf-8')), t1 - t0)

        socket_mgr._channel = self.twitch_channel.lower().lstrip("#")
        socket_mgr._running = True

        socket_mgr.ws = websocket.WebSocketApp(
            "wss://irc-ws.chat.twitch.tv:443",
            on_open=socket_mgr._on_open,
            on_message=on_raw_message_benchmark,
            on_error=socket_mgr._on_error,
            on_close=socket_mgr._on_close
        )

        while not self.stop_event.is_set():
            socket_mgr.ws.run_forever(ping_interval=30, ping_timeout=10)
            if not self.stop_event.is_set():
                time.sleep(2)

    def print_dashboard(self):
        k = self.kick_stats.get_metrics()
        t = self.twitch_stats.get_metrics()

        header = f"\n📊 --- LIVE CHAT PERFORMANCE BENCHMARK --- ({datetime.now().strftime('%H:%M:%S')})"
        sep = "=" * 80
        table = f"""
{header}
{sep}
| Metric                      | Kick (Pusher WS)           | Twitch (IRC WS)           |
+-----------------------------+----------------------------+---------------------------+
| Target Channel              | #{self.kick_channel:<25} | #{self.twitch_channel:<25} |
| Total Messages Received     | {k['total_messages']:<26} | {t['total_messages']:<25} |
| Overall Throughput (msg/s)  | {k['overall_msg_sec']:<26.2f} | {t['overall_msg_sec']:<25.2f} |
| Recent Rate (Last 5s msg/s) | {k['recent_msg_sec']:<26.2f} | {t['recent_msg_sec']:<25.2f} |
| Avg Payload Size (Bytes)    | {k['avg_bytes_per_msg']:<26.1f} | {t['avg_bytes_per_msg']:<25.1f} |
| Avg Parse Latency (μs)      | {k['avg_latency_us']:<26.2f} | {t['avg_latency_us']:<25.2f} |
| Min / Max Latency (μs)      | {f"{k['min_latency_us']:.1f} / {k['max_latency_us']:.1f}":<26} | {f"{t['min_latency_us']:.1f} / {t['max_latency_us']:.1f}":<25} |
{sep}
"""
        self._log(table)

    def start_benchmark(self):
        self._init_logfile()
        self._log(f"🚀 Initializing Concurrent Live Benchmark...")
        self._log(f"🟢 Kick Channel: '{self.kick_channel}' | 🟣 Twitch Channel: '{self.twitch_channel}'")

        try:
            kick_room_id = fetch_kick_room_id(self.kick_channel)
            self._log(f"✅ Kick Room ID resolved: {kick_room_id}")
        except Exception as e:
            self._log(f"⚠️ Failed resolving Kick channel '{self.kick_channel}': {e}. Falling back to 'xqc'")
            self.kick_channel = "xqc"
            kick_room_id = fetch_kick_room_id("xqc")

        kick_thread = threading.Thread(target=self.run_kick, args=(kick_room_id,), daemon=True)
        twitch_thread = threading.Thread(target=self.run_twitch, daemon=True)

        kick_thread.start()
        twitch_thread.start()

        start_t = time.time()
        try:
            while not self.stop_event.is_set():
                time.sleep(5)
                self.print_dashboard()

                if self.duration > 0 and (time.time() - start_t) >= self.duration:
                    self._log(f"⏱️ Specified benchmark duration ({self.duration}s) reached. Stopping...")
                    break
        except KeyboardInterrupt:
            self._log("\n🛑 Benchmark interrupted by user.")
        finally:
            self.stop_event.set()
            self._log("\n🏁 FINAL BENCHMARK SUMMARY REPORT:")
            self.print_dashboard()
            if self.log_file_handle:
                self.log_file_handle.close()

def main():
    parser = argparse.ArgumentParser(description="Live Concurrent Chat Performance Benchmark (Kick vs Twitch)")
    parser.add_argument("--kick-channel", type=str, default="xqc", help="Kick channel slug (default: xqc)")
    parser.add_argument("--twitch-channel", type=str, default="xqc", help="Twitch channel name (default: xqc)")
    parser.add_argument("--duration", type=int, default=0, help="Benchmark duration in seconds (0 = run indefinitely until Ctrl+C)")
    parser.add_argument("--no-log", action="store_true", help="Disable saving benchmark log to file")

    args = parser.parse_args()

    runner = ChatBenchmarkRunner(
        kick_channel=args.kick_channel,
        twitch_channel=args.twitch_channel,
        duration=args.duration,
        log_enabled=not args.no_log
    )
    runner.start_benchmark()

if __name__ == "__main__":
    main()
