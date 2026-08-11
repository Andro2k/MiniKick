# tests\test_twitch_websocket_live.py

import os
import json
import time
import argparse
import websocket
from datetime import datetime

class TwitchWebsocketInspector:
    def __init__(self, channel_name: str = "xqc", oauth_token: str = "", nick: str = "", raw_mode: bool = False, save_log: bool = True, log_path: str = None):
        self.channel_name = channel_name.lower().replace("#", "").strip()
        self.token = oauth_token or "justinfan12345"
        self.nick = nick.lower() if nick else ("justinfan12345" if self.token.startswith("justinfan") else "justinfan12345")
        self.raw_mode = raw_mode
        self.save_log = save_log
        self.log_filepath = log_path
        self.log_file_handle = None
        self.ws = None
        self.event_counts = {}
        self.start_time = None

    def _log(self, text: str):
        print(text)
        if self.log_file_handle:
            try:
                self.log_file_handle.write(text + "\n")
                self.log_file_handle.flush()
            except Exception:
                pass

    def _init_logging_file(self):
        if not self.save_log:
            return
        try:
            logs_dir = os.path.join(os.path.dirname(__file__), "logs")
            os.makedirs(logs_dir, exist_ok=True)
            if not self.log_filepath:
                dt_tag = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                self.log_filepath = os.path.join(logs_dir, f"ws_twitch_{self.channel_name}_{dt_tag}.log")

            self.log_file_handle = open(self.log_filepath, "a", encoding="utf-8")
            self._log(f"📝 Registrando sesión en archivo: {os.path.abspath(self.log_filepath)}")
        except Exception as e:
            print(f"⚠️ No se pudo iniciar el archivo de log: {e}")

    def _parse_irc_line(self, raw_line: str) -> dict:
        tags = {}
        line = raw_line

        if line.startswith("@"):
            tag_part, line = line[1:].split(" ", 1)
            for pair in tag_part.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    v = v.replace(r"\s", " ").replace(r"\:", ";").replace(r"\\", "\\").replace(r"\r", "\r").replace(r"\n", "\n")
                    tags[k] = v
                else:
                    tags[pair] = ""

        prefix = ""
        if line.startswith(":"):
            prefix, line = line[1:].split(" ", 1)

        command = ""
        params = []
        if " " in line:
            parts = line.split(" ", 1)
            command = parts[0]
            remainder = parts[1]
            if " :" in remainder:
                args_part, trailing = remainder.split(" :", 1)
                params = args_part.split()
                params.append(trailing)
            else:
                params = remainder.split()
        else:
            command = line

        return {
            "raw": raw_line,
            "tags": tags,
            "prefix": prefix,
            "command": command,
            "params": params
        }

    def start(self):
        self._init_logging_file()

        ws_url = "wss://irc-ws.chat.twitch.tv:443"
        self._log(f"🚀 Conectando a Twitch IRC WebSocket ({ws_url})...")
        self._log(f"📺 Canal destino: #{self.channel_name} | Nick: {self.nick}")
        mode_str = "📦 MODO RAW (IRC RAW 100% EN CRUDO)" if self.raw_mode else "💬 MODO RESUMIDO Y FORMATEADO"
        self._log(f"💡 {mode_str} activo. Presione Ctrl+C para salir.\n" + "="*70)

        self.start_time = time.time()
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever(ping_interval=30, ping_timeout=10)

    def _on_open(self, ws):
        now_str = datetime.now().strftime('%H:%M:%S')
        self._log(f"🟢 Conexión WebSocket establecida con éxito ({now_str})")
        self._log("📡 Solicitando capacidades extendidas (tags, commands, membership)...")
        ws.send("CAP REQ :twitch.tv/tags twitch.tv/commands twitch.tv/membership\r\n")

        pass_token = f"oauth:{self.token}" if not self.token.startswith("oauth:") else self.token
        ws.send(f"PASS {pass_token}\r\n")
        ws.send(f"NICK {self.nick}\r\n")
        ws.send(f"JOIN #{self.channel_name}\r\n")

    def _on_message(self, ws, raw: str):
        lines = raw.strip().split("\r\n")
        now_str = datetime.now().strftime('%H:%M:%S')

        for raw_line in lines:
            if not raw_line:
                continue

            if raw_line.startswith("PING"):
                ws.send(raw_line.replace("PING", "PONG"))
                self.event_counts["PING"] = self.event_counts.get("PING", 0) + 1
                continue

            parsed = self._parse_irc_line(raw_line)
            cmd = parsed["command"]
            tags = parsed["tags"]
            params = parsed["params"]

            self.event_counts[cmd] = self.event_counts.get(cmd, 0) + 1

            if self.raw_mode:
                self._log(f"\n📦 [{now_str}] IRC COMMAND: '{cmd}'")
                self._log(f"RAW: {raw_line}")
                if tags:
                    self._log(f"TAGS: {json.dumps(tags, indent=2, ensure_ascii=False)}")
                continue

            if cmd == "PRIVMSG":
                sender = tags.get("display-name") or (parsed["prefix"].split("!")[0] if "!" in parsed["prefix"] else "Desconocido")
                message = params[-1] if params else ""
                badges_raw = tags.get("badges", "")
                badges = [b.split("/")[0] for b in badges_raw.split(",") if b]
                badge_str = f"[{', '.join(badges)}]" if badges else ""
                color = tags.get("color", "#9146FF")
                user_id = tags.get("user-id", "")
                mod = tags.get("mod", "0")
                sub = tags.get("subscriber", "0")

                sub_tag = "⭐" if sub == "1" else ""
                mod_tag = "🛡️" if mod == "1" else ""
                self._log(f"💬 [{now_str}] {mod_tag}{sub_tag}{badge_str} {sender} (ID:{user_id}): {message}")

            elif cmd == "USERNOTICE":
                msg_id = tags.get("msg-id", "")
                system_msg = tags.get("system-msg", "").replace(r"\s", " ")
                sender = tags.get("display-name", "Anónimo")

                if msg_id in ("sub", "resub"):
                    months = tags.get("msg-param-cumulative-months", "1")
                    self._log(f"⭐ [{now_str}] ¡SUSCRIPCIÓN! {sender} ({months} meses) - {system_msg}")
                elif msg_id in ("subgift", "anonsubgift"):
                    recipient = tags.get("msg-param-recipient-display-name", "Alguien")
                    self._log(f"🎁 [{now_str}] ¡REGALO DE SUB! {sender} le regaló una sub a {recipient}!")
                elif msg_id == "raid":
                    viewers = tags.get("msg-param-viewerCount", "0")
                    self._log(f"🚀 [{now_str}] ¡RAID! {sender} inició una raid con {viewers} espectadores!")
                else:
                    self._log(f"🎉 [{now_str}] USERNOTICE ({msg_id}): {system_msg or sender}")

            elif cmd == "CLEARCHAT":
                target_user = params[-1] if params else "Chat"
                ban_duration = tags.get("ban-duration")
                if ban_duration:
                    self._log(f"⏱️ [{now_str}] TIMEOUT: {target_user} sancionado por {ban_duration}s")
                else:
                    self._log(f"🚫 [{now_str}] BAN PERMANENTE: {target_user} fue baneado")

            elif cmd == "CLEARMSG":
                deleted_msg = params[-1] if params else ""
                login = tags.get("login", "")
                self._log(f"🗑️ [{now_str}] MENSAJE ELIMINADO de @{login}: '{deleted_msg}'")

            elif cmd == "NOTICE":
                notice_msg = params[-1] if params else ""
                self._log(f"ℹ️ [{now_str}] AVISO DE CHAT: {notice_msg}")

            elif cmd == "JOIN":
                channel = params[0] if params else f"#{self.channel_name}"
                self._log(f"🟢 [{now_str}] Unido exitosamente al canal {channel}")

            elif cmd in ("001", "002", "003", "004", "375", "372", "376", "CAP"):
                pass

            else:
                self._log(f"⚡ [{now_str}] COMANDO IRC RECIBIDO: '{cmd}' -> {params}")

    def _on_error(self, ws, error):
        self._log(f"❌ Error de WebSocket Twitch: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self._log(f"\n🔴 Conexión cerrada. ({close_status_code}: {close_msg})")
        self._print_stats()

    def _print_stats(self):
        if not self.start_time:
            return
        elapsed = max(1.0, time.time() - self.start_time)
        self._log("\n" + "="*70)
        self._log("📊 RESUMEN DE LA PRUEBA WEBSOCKET DE TWITCH IRC")
        self._log("="*70)
        self._log(f"⏱️ Tiempo transcurrido: {int(elapsed)} segundos")
        self._log(f"📺 Canal inspeccionado: #{self.channel_name}")
        self._log("📈 Comandos/Eventos IRC Recibidos:")
        for ev, count in sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True):
            self._log(f"  • {ev}: {count}")
        chat_count = self.event_counts.get("PRIVMSG", 0)
        msg_per_min = round((chat_count / elapsed) * 60, 2)
        self._log(f"💬 Promedio de chat: {msg_per_min} msgs/minuto")
        if self.log_filepath:
            self._log(f"📁 Log guardado en: {os.path.abspath(self.log_filepath)}")
        self._log("="*70)

        if self.log_file_handle:
            try:
                self.log_file_handle.close()
                self.log_file_handle = None
            except Exception:
                pass

def main():
    parser = argparse.ArgumentParser(description="Twitch IRC WebSocket Real-Time Test & Event Inspector")
    parser.add_argument("--channel", type=str, default="xqc", help="Nombre del canal de Twitch (ej: xqc, ibai, alexelcapo)")
    parser.add_argument("--token", type=str, default="", help="OAuth Token de Twitch (opcional, por defecto usa nick anónimo justinfan)")
    parser.add_argument("--nick", type=str, default="", help="Nombre de usuario del bot (opcional)")
    parser.add_argument("--raw", "-r", action="store_true", help="Mostrar líneas IRC y JSON de tags 100%% en crudo")
    parser.add_argument("--no-log", action="store_true", help="Desactivar la creación del archivo de log")
    parser.add_argument("--log-path", type=str, default=None, help="Ruta personalizada para guardar el archivo de log")

    args = parser.parse_args()

    inspector = TwitchWebsocketInspector(
        channel_name=args.channel,
        oauth_token=args.token,
        nick=args.nick,
        raw_mode=args.raw,
        save_log=not args.no_log,
        log_path=args.log_path
    )
    try:
        inspector.start()
    except KeyboardInterrupt:
        print("\n👋 Prueba interrumpida por el usuario.")
        inspector._print_stats()

if __name__ == "__main__":
    main()
