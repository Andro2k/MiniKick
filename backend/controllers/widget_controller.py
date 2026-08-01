# backend\controllers\widget_controller.py

import logging
from PySide6.QtCore import QObject, Slot, Signal
from backend.services import WidgetService, CommandService

logger = logging.getLogger("minikick.controllers.widgets")

class WidgetController(QObject):
    death_count_updated = Signal(int)
    score_updated = Signal(int, int)
    widgets_reloaded = Signal(dict)

    PLUGIN_TAGS = {
        "shoutout": "[PLUGIN_WIDGET_SO]",
        "death": "[PLUGIN_WIDGET_DEATH]",
        "score": "[PLUGIN_WIDGET_SCORE]"
    }

    def __init__(self, view, widget_service: WidgetService, command_service: CommandService, overlay_server=None, i18n=None):
        super().__init__()
        self.view = view
        self.widget_service = widget_service
        self.command_service = command_service
        self.overlay_server = overlay_server
        self.i18n = i18n

        self._widget_handlers = {
            self.PLUGIN_TAGS["shoutout"]: lambda user, args, first_word, prefix: self._process_shoutout(user, args, prefix),
            self.PLUGIN_TAGS["death"]: lambda user, args, first_word, prefix: self._process_death(user, args or first_word),
            self.PLUGIN_TAGS["score"]: self._dispatch_score_command,
        }

        self._connect_signals()
        self.sync_commands_with_db()

    def _connect_signals(self):
        if self.view:
            self.view.widget_saved.connect(self.handle_widget_save)
            self.view.death_count_changed.connect(self.handle_death_count_change)
            self.view.score_changed.connect(self.handle_score_change)
            self.death_count_updated.connect(self.view.update_death_count_display)
            self.score_updated.connect(self.view.update_score_display)

    def load_initial_data(self):
        widgets = self.widget_service.get_all_widgets()
        if self.view:
            self.view.populate_widgets(widgets)

    def sync_commands_with_db(self):
        widgets = self.widget_service.get_all_widgets()
        for w_id, data in widgets.items():
            tag = self.PLUGIN_TAGS.get(w_id)
            if not tag:
                continue
            
            cmd_name = data.get("command", "").strip()
            if not cmd_name:
                continue

            if not cmd_name.startswith("!"):
                cmd_name = "!" + cmd_name

            is_active = data.get("is_active", True)
            cooldown = data.get("cooldown", 3)
            perm = data.get("permission", "everyone")

            aliases = ""
            if w_id == "score":
                aliases = "!win, !loss, !lose, !victoria, !derrota"
            elif w_id == "death":
                aliases = "!muerte, !death, !deaths, !muertes"
            elif w_id == "shoutout":
                aliases = "!shoutout"

            self.command_service.save_command(
                trigger=cmd_name,
                response=tag,
                is_active=is_active,
                cooldown=cooldown,
                aliases=aliases,
                is_regex=False,
                permission=perm
            )

    @Slot(str, bool, str, int, str, dict)
    def handle_widget_save(self, widget_id: str, is_active: bool, command: str, cooldown: int, permission: str, config: dict):
        self.widget_service.save_widget(widget_id, is_active, command, cooldown, permission, config)
        self.sync_commands_with_db()

    @Slot(int)
    def handle_death_count_change(self, new_val: int):
        final_val = self.widget_service.update_death_count(set_val=new_val)
        self.death_count_updated.emit(final_val)
        if self.overlay_server:
            title_text = self.i18n.get("widgets.death.overlay_title")
            self.overlay_server.trigger_widget_event("death_update", {
                "count": final_val,
                "title_text": title_text
            })

    @Slot(int, int)
    def handle_score_change(self, wins: int, losses: int):
        final_wins, final_losses = self.widget_service.update_score(set_wins=wins, set_losses=losses)
        self.score_updated.emit(final_wins, final_losses)
        if self.overlay_server:
            title_text = self.i18n.get("widgets.score.overlay_title")
            self.overlay_server.trigger_widget_event("score", {
                "wins": final_wins,
                "losses": final_losses,
                "title_text": title_text
            })

    def _dispatch_score_command(self, user: str, args: str, first_word: str, prefix: str) -> None:
        arg_clean = args.strip().lower()

        if arg_clean in ("reset", "0", "reiniciar", "clear"):
            wins, losses = self.widget_service.update_score(reset=True)
            msg = self.i18n.get("widgets.score.msg_reset").replace("{user}", user)
            self._notify_score_change(wins, losses, msg)
            return

        if first_word in ("win", "w", "victoria"):
            if arg_clean in ("-1", "-", "sub", "restar"):
                wins, losses = self.widget_service.update_score(delta_wins=-1)
            else:
                wins, losses = self.widget_service.update_score(delta_wins=1)
            msg = self.i18n.get("widgets.score.msg_win").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
            self._notify_score_change(wins, losses, msg)
            return

        if first_word in ("loss", "lose", "l", "derrota"):
            if arg_clean in ("-1", "-", "sub", "restar"):
                wins, losses = self.widget_service.update_score(delta_losses=-1)
            else:
                wins, losses = self.widget_service.update_score(delta_losses=1)
            msg = self.i18n.get("widgets.score.msg_loss").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
            self._notify_score_change(wins, losses, msg)
            return

        if arg_clean in ("+1", "+", "win", "w", "victoria"):
            wins, losses = self.widget_service.update_score(delta_wins=1)
            msg = self.i18n.get("widgets.score.msg_win").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
        elif arg_clean in ("-1", "-", "loss", "lose", "l", "derrota"):
            wins, losses = self.widget_service.update_score(delta_losses=1)
            msg = self.i18n.get("widgets.score.msg_loss").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
        else:
            wins, losses = self.widget_service.get_score()
            msg = self.i18n.get("widgets.score.msg_check").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))

        self._notify_score_change(wins, losses, msg)

    def _notify_score_change(self, wins: int, losses: int, msg: str) -> None:
        self.score_updated.emit(wins, losses)
        if self.overlay_server:
            title_text = self.i18n.get("widgets.score.overlay_title")
            self.overlay_server.trigger_widget_event("score", {
                "wins": wins,
                "losses": losses,
                "title_text": title_text
            })
        self.command_service.send_response(msg)

    @Slot(str, str, str, str)
    def handle_widget_command(self, plugin_tag: str, user: str, content: str, prefix: str):
        parts = content.strip().split()
        first_word = parts[0][len(prefix):].lower() if parts else ""
        args = " ".join(parts[1:]).strip() if len(parts) > 1 else ""

        handler = self._widget_handlers.get(plugin_tag)
        if handler:
            handler(user, args, first_word, prefix)

    def _process_shoutout(self, user: str, args: str, prefix: str):
        if not args:
            err_msg = self.i18n.get("widgets.so.usage_error").replace("{user}", user).replace("{trigger}", prefix)
            self.command_service.send_response(err_msg)
            return

        target_user = args.split()[0].lstrip("@").strip()
        reply = self.widget_service.format_shoutout(target_user)
        self.command_service.send_response(reply)

        if self.overlay_server:
            import threading
            def _fetch_and_trigger():
                avatar_url = self.widget_service.fetch_streamer_avatar(target_user)
                header_text = self.i18n.get("widgets.so.overlay_header")
                self.overlay_server.trigger_widget_event("shoutout", {
                    "target": target_user,
                    "url": f"https://kick.com/{target_user}",
                    "avatar_url": avatar_url,
                    "header_text": header_text
                })

            threading.Thread(target=_fetch_and_trigger, daemon=True).start()

    def _process_death(self, user: str, args: str):
        arg_clean = args.strip().lower()
        if arg_clean in ("reset", "0", "reiniciar", "clear"):
            new_count = self.widget_service.update_death_count(set_val=0)
            msg = self.i18n.get("widgets.death.msg_reset").replace("{user}", user).replace("{count}", str(new_count))
        elif arg_clean in ("-", "sub", "restar", "-1"):
            new_count = self.widget_service.update_death_count(delta=-1)
            msg = self.i18n.get("widgets.death.msg_sub").replace("{user}", user).replace("{count}", str(new_count))
        elif arg_clean in ("+", "add", "sumar", "1", "muerte", "+1", ""):
            new_count = self.widget_service.update_death_count(delta=1)
            msg = self.i18n.get("widgets.death.msg_add").replace("{user}", user).replace("{count}", str(new_count))
        elif arg_clean in ("check", "status", "ver"):
            new_count = self.widget_service.get_death_count()
            msg = self.i18n.get("widgets.death.msg_check").replace("{user}", user).replace("{count}", str(new_count))
        else:
            try:
                val = int(arg_clean)
                new_count = self.widget_service.update_death_count(set_val=max(0, val))
                msg = self.i18n.get("widgets.death.msg_add").replace("{user}", user).replace("{count}", str(new_count))
            except ValueError:
                new_count = self.widget_service.update_death_count(delta=1)
                msg = self.i18n.get("widgets.death.msg_add").replace("{user}", user).replace("{count}", str(new_count))

        self.death_count_updated.emit(new_count)
        if self.overlay_server:
            title_text = self.i18n.get("widgets.death.overlay_title")
            self.overlay_server.trigger_widget_event("death_update", {
                "count": new_count,
                "title_text": title_text
            })
        self.command_service.send_response(msg)
