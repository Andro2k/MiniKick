# backend\controllers\widget_controller.py

import json
import logging
import re
import threading
import time
from PySide6.QtCore import QObject, Slot, Signal, QTimer
from backend.services import WidgetService, CommandService

logger = logging.getLogger("minikick.controllers.widgets")

_WIDGET_DEFAULT_ALIASES: dict[str, str] = {
    "score": "!win, !loss, !lose, !victoria, !derrota",
    "death": "!muerte, !death, !deaths, !muertes",
    "shoutout": "!shoutout",
}

_WIDGET_TITLE_KEYS: dict[str, str] = {
    "shoutout": "widgets.so.title",
    "death": "widgets.death.title",
    "score": "widgets.score.title",
}

_RESET_COMMANDS: frozenset[str] = frozenset({"reset", "0", "reiniciar", "clear"})
_SCORE_WIN_WORDS: frozenset[str] = frozenset({"win", "w", "victoria"})
_SCORE_LOSS_WORDS: frozenset[str] = frozenset({"loss", "lose", "l", "derrota"})
_DELTA_DECREMENT: frozenset[str] = frozenset({"-1", "-", "sub", "restar"})
_SCORE_PLUS_WORDS: frozenset[str] = frozenset({"+1", "+", "win", "w", "victoria"})
_SCORE_MINUS_WORDS: frozenset[str] = frozenset({"-1", "-", "loss", "lose", "l", "derrota"})

_DEATH_SUB_WORDS: frozenset[str] = frozenset({"-", "sub", "restar", "-1"})
_DEATH_ADD_WORDS: frozenset[str] = frozenset({"+", "add", "sumar", "1", "muerte", "+1", ""})
_DEATH_CHECK_WORDS: frozenset[str] = frozenset({"check", "status", "ver"})


class WidgetController(QObject):
    death_count_updated = Signal(int)
    score_updated = Signal(int, int)
    widgets_reloaded = Signal(object)

    PLUGIN_TAGS = {
        "shoutout": "[PLUGIN_WIDGET_SO]", "death": "[PLUGIN_WIDGET_DEATH]", "score": "[PLUGIN_WIDGET_SCORE]",
        "explosion": "[PLUGIN_WIDGET_EXPLOSION]", "combo": "[PLUGIN_WIDGET_COMBO]"
    }

    _KICK_EMOTE_REGEX = re.compile(r"\[emote:(?:(\d+):)?([^\]]+)\]")
    _EMOJI_REGEX = re.compile(r"[\U00010000-\U0010ffff\u2600-\u27bf]")

    def __init__(self, view, widget_service: WidgetService, command_service: CommandService, overlay_server=None, i18n=None, toast_manager=None):
        super().__init__()
        self.view = view
        self.widget_service = widget_service
        self.command_service = command_service
        self.overlay_server = overlay_server
        from backend.services.system import TranslationService
        self.i18n = i18n or TranslationService()
        self.toast = toast_manager

        self._last_combo_emote = ""
        self._last_combo_time = 0.0
        self._combo_count = 0
        self._view_connected = False

        self._widget_handlers = {
            self.PLUGIN_TAGS["shoutout"]: lambda user, args, action_word, prefix, platform: self._process_shoutout(user, args, prefix, platform=platform),
            self.PLUGIN_TAGS["death"]: lambda user, args, action_word, prefix, platform: self._process_death(user, args, action_word, platform=platform),
            self.PLUGIN_TAGS["score"]: lambda user, args, action_word, prefix, platform: self._dispatch_score_command(user, args, action_word, prefix, platform=platform),
            self.PLUGIN_TAGS["explosion"]: lambda user, args, action_word, prefix, platform: self._process_explosion_command(user, args, platform=platform),
            self.PLUGIN_TAGS["combo"]: lambda user, args, action_word, prefix, platform: self._process_combo_command(user, args, platform=platform),
        }

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._flush_saves)
        self._pending_saves = set()
        self._is_syncing_db = False
        self._needs_reload = False

        self.command_service.commands_changed.connect(self._sync_widgets_from_commands_db)
        if self.view is not None:
            self._connect_signals()
        self.sync_commands_with_db()

    def attach_view(self, view) -> None:
        self.view = view
        if self.view is not None:
            self._connect_signals()
            self.load_initial_data()

    def _trigger_deferred_save(self, widget_id: str):
        self._pending_saves.add(widget_id)
        self._save_timer.start()

    def _flush_saves(self):
        saved_ids = list(self._pending_saves)
        self._pending_saves.clear()
        for w_id in saved_ids:
            w = self.widget_service.get_widget(w_id)
            if w:
                self.widget_service.save_widget(
                    widget_id=w_id,
                    is_active=w.get("is_active", True),
                    command=w.get("command", ""),
                    cooldown=w.get("cooldown", 3),
                    permission=w.get("permission", "everyone"),
                    config=w.get("config", {}),
                    defer_disk=False
                )
                self._sync_single_widget_command(w_id, w)

    def _connect_signals(self):
        if not self.view or self._view_connected:
            return
        self._view_connected = True
        self.view.widget_saved.connect(self.handle_widget_save)
        self.view.death_count_changed.connect(self.handle_death_count_change)
        self.view.score_changed.connect(self.handle_score_change)
        self.death_count_updated.connect(self.view.update_death_count_display)
        self.score_updated.connect(self.view.update_score_display)
        if hasattr(self.view, "view_shown"):
            self.view.view_shown.connect(self._on_view_shown)

    def _on_view_shown(self):
        if self._needs_reload:
            self._needs_reload = False
            if self.view:
                self.view.populate_widgets(self.widget_service.get_all_widgets())

    def load_initial_data(self):
        widgets = self.widget_service.get_all_widgets()
        if self.view:
            self.view.populate_widgets(widgets)

        if self.overlay_server:
            death_w = widgets.get("death", {})
            score_w = widgets.get("score", {})
            title_death = self.i18n.get("widgets.death.overlay_title")
            title_score = self.i18n.get("widgets.score.overlay_title")

            self.overlay_server.trigger_widget_event("death_update", {
                "count": death_w.get("config", {}).get("count", 0),
                "is_active": death_w.get("is_active", True),
                "title_text": title_death
            })

            self.overlay_server.trigger_widget_event("score", {
                "wins": score_w.get("config", {}).get("wins", 0),
                "losses": score_w.get("config", {}).get("losses", 0),
                "is_active": score_w.get("is_active", True),
                "title_text": title_score
            })


    def _sync_widgets_from_commands_db(self):
        if getattr(self, "_is_syncing_db", False):
            return
        self._is_syncing_db = True
        try:
            commands = self.command_service.get_all_commands()
            tag_map = {c["response"]: c for c in commands if isinstance(c, dict) and "response" in c}
            widgets = self.widget_service.get_all_widgets()
            changed = False

            for w_id, w_data in widgets.items():
                tag = self.PLUGIN_TAGS.get(w_id)
                if not tag or tag not in tag_map:
                    continue
                
                cmd_info = tag_map[tag]
                is_active = cmd_info.get("is_active", True)
                cmd_trigger = cmd_info.get("trigger", "")
                cooldown = cmd_info.get("cooldown", 3)
                perm = cmd_info.get("permission", "everyone")

                if (w_data.get("is_active") != is_active or 
                    w_data.get("command") != cmd_trigger or 
                    w_data.get("cooldown") != cooldown or 
                    w_data.get("permission") != perm):
                    
                    w_data["is_active"] = is_active
                    w_data["command"] = cmd_trigger
                    w_data["cooldown"] = cooldown
                    w_data["permission"] = perm
                    
                    self.widget_service.save_widget(
                        w_id, is_active, cmd_trigger, cooldown, perm, w_data.get("config", {})
                    )
                    changed = True

            if self.view:
                if self.view.isVisible():
                    self._needs_reload = False
                    self.view.populate_widgets(self.widget_service.get_all_widgets())
                else:
                    self._needs_reload = True
        finally:
            self._is_syncing_db = False

    def _sync_single_widget_command(self, w_id: str, data: dict | None = None) -> None:
        tag = self.PLUGIN_TAGS.get(w_id)
        if not tag:
            return

        if data is None:
            data = self.widget_service.get_widget(w_id)
        if not data:
            return

        cmd_name = data.get("command", "").strip()
        if not cmd_name:
            return

        if not cmd_name.startswith("!"):
            cmd_name = "!" + cmd_name

        is_active = data.get("is_active", True)
        cooldown = data.get("cooldown", 3)
        perm = data.get("permission", "everyone")

        aliases = _WIDGET_DEFAULT_ALIASES.get(w_id, "")

        existing_cmd = self.command_service.get_command_by_trigger(cmd_name)
        if existing_cmd:
            if (existing_cmd.get("response") == tag and
                existing_cmd.get("is_active") == is_active and
                existing_cmd.get("cooldown") == cooldown and
                existing_cmd.get("permission") == perm and
                existing_cmd.get("aliases") == aliases):
                return

        apply_k = existing_cmd.get("apply_kick", True) if existing_cmd else True
        apply_tw = existing_cmd.get("apply_twitch", True) if existing_cmd else True
        apply_yt = existing_cmd.get("apply_youtube", True) if existing_cmd else True
        apply_tk = existing_cmd.get("apply_tiktok", True) if existing_cmd else True

        self.command_service.save_command(
            trigger=cmd_name,
            response=tag,
            is_active=is_active,
            cooldown=cooldown,
            aliases=aliases,
            is_regex=False,
            permission=perm,
            apply_kick=apply_k,
            apply_twitch=apply_tw,
            apply_youtube=apply_yt,
            apply_tiktok=apply_tk
        )

    def sync_commands_with_db(self):
        if getattr(self, "_is_syncing_db", False):
            return
        self._is_syncing_db = True
        try:
            widgets = self.widget_service.get_all_widgets()
            for w_id, data in widgets.items():
                self._sync_single_widget_command(w_id, data)
        finally:
            self._is_syncing_db = False

    @Slot(str, bool, str, int, str, object)
    def handle_widget_save(self, widget_id: str, is_active: bool, command: str, cooldown: int, permission: str, config: dict):
        previous = self.widget_service.get_widget(widget_id)
        was_active = previous.get("is_active", True) if previous else True
        config_dict = dict(config)

        if previous and (
            previous.get("is_active") == is_active and
            previous.get("command") == command and
            previous.get("cooldown") == cooldown and
            previous.get("permission") == permission and
            previous.get("config") == config_dict
        ):
            return

        logger.info("[User Action] Updated widget '%s': is_active=%s, command='%s', cooldown=%d, perm='%s', config=%s",
                    widget_id, is_active, command, cooldown, permission, config_dict)

        self.widget_service.save_widget(
            widget_id=widget_id,
            is_active=is_active,
            command=command,
            cooldown=cooldown,
            permission=permission,
            config=config_dict,
            defer_disk=True
        )

        if was_active != is_active:
            title_key = "widgets.status.activated" if is_active else "widgets.status.deactivated"
            msg_key = "widgets.status.activated_msg" if is_active else "widgets.status.deactivated_msg"
            
            title_k = _WIDGET_TITLE_KEYS.get(widget_id)
            w_name = self.i18n.get(title_k) if title_k else widget_id
            
            title = self.i18n.get(title_key)
            message = self.i18n.get(msg_key).replace("{widget_name}", w_name)
            state = "success" if is_active else "info"

            if self.toast:
                self.toast.show_toast(
                    title=title,
                    message=message,
                    state=state,
                    tag=f"widget_{widget_id}"
                )

            if self.overlay_server:
                self.overlay_server.trigger_widget_event("widget_toggle", {
                    "widget_id": widget_id,
                    "is_active": is_active
                })

        self._trigger_deferred_save(widget_id)

    @Slot(int)
    def handle_death_count_change(self, new_val: int):
        logger.info("[User Action] Manual death counter change: count=%d", new_val)
        final_val = self.widget_service.update_death_count(set_val=new_val, defer_disk=True)
        self.death_count_updated.emit(final_val)
        self._trigger_deferred_save("death")
        if self.overlay_server:
            w_death = self.widget_service.get_widget("death")
            title_text = self.i18n.get("widgets.death.overlay_title")
            self.overlay_server.trigger_widget_event("death_update", {
                "count": final_val,
                "is_active": w_death.get("is_active", True),
                "title_text": title_text
            })

    @Slot(int, int)
    def handle_score_change(self, wins: int, losses: int):
        logger.info("[User Action] Manual score counter change: wins=%d, losses=%d", wins, losses)
        final_wins, final_losses = self.widget_service.update_score(set_wins=wins, set_losses=losses, defer_disk=True)
        self.score_updated.emit(final_wins, final_losses)
        self._trigger_deferred_save("score")
        if self.overlay_server:
            w_score = self.widget_service.get_widget("score")
            title_text = self.i18n.get("widgets.score.overlay_title")
            self.overlay_server.trigger_widget_event("score", {
                "wins": final_wins,
                "losses": final_losses,
                "is_active": w_score.get("is_active", True),
                "title_text": title_text
            })

    def _dispatch_score_command(self, user: str, args: str, action_word: str, prefix: str, platform: str = "kick") -> None:
        arg_clean = args.strip().lower()

        if arg_clean in _RESET_COMMANDS or action_word in _RESET_COMMANDS:
            wins, losses = self.widget_service.update_score(reset=True)
            msg = self.i18n.get("widgets.score.msg_reset").replace("{user}", user)
            self._notify_score_change(wins, losses, msg, platform=platform)
            return

        if action_word in _SCORE_WIN_WORDS or (action_word == "score" and arg_clean in _SCORE_WIN_WORDS):
            delta = -1 if arg_clean in _DELTA_DECREMENT else 1
            wins, losses = self.widget_service.update_score(delta_wins=delta)
            msg = self.i18n.get("widgets.score.msg_win").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
            self._notify_score_change(wins, losses, msg, platform=platform)
            return

        if action_word in _SCORE_LOSS_WORDS or (action_word == "score" and arg_clean in _SCORE_LOSS_WORDS):
            delta = -1 if arg_clean in _DELTA_DECREMENT else 1
            wins, losses = self.widget_service.update_score(delta_losses=delta)
            msg = self.i18n.get("widgets.score.msg_loss").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
            self._notify_score_change(wins, losses, msg, platform=platform)
            return

        if arg_clean in _SCORE_PLUS_WORDS or action_word.endswith("+"):
            wins, losses = self.widget_service.update_score(delta_wins=1)
            msg = self.i18n.get("widgets.score.msg_win").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
        elif arg_clean in _SCORE_MINUS_WORDS or action_word.endswith("-"):
            wins, losses = self.widget_service.update_score(delta_losses=1)
            msg = self.i18n.get("widgets.score.msg_loss").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))
        else:
            wins, losses = self.widget_service.get_score()
            msg = self.i18n.get("widgets.score.msg_check").replace("{user}", user).replace("{wins}", str(wins)).replace("{losses}", str(losses))

        self._notify_score_change(wins, losses, msg, platform=platform)

    def _notify_score_change(self, wins: int, losses: int, msg: str, platform: str = "kick") -> None:
        self.score_updated.emit(wins, losses)
        if self.overlay_server:
            w_score = self.widget_service.get_widget("score")
            title_text = self.i18n.get("widgets.score.overlay_title")
            self.overlay_server.trigger_widget_event("score", {
                "wins": wins,
                "losses": losses,
                "is_active": w_score.get("is_active", True),
                "title_text": title_text
            })
        self.command_service.send_response(msg, platform=platform)

    @Slot(str, str, str, str, str)
    def handle_widget_command(self, plugin_tag: str, user: str, content: str, prefix: str, platform: str = "kick"):
        parts = content.strip().split()
        cmd_trigger = prefix.lstrip("!").lower()
        suffix = parts[0][len(prefix):].lower() if parts else ""
        action_word = cmd_trigger or suffix
        args = " ".join(parts[1:]).strip() if len(parts) > 1 else ""

        handler = self._widget_handlers.get(plugin_tag)
        if handler:
            handler(user, args, action_word, prefix, platform)

    def _process_shoutout(self, user: str, args: str, prefix: str, platform: str = "kick"):
        arg_words = args.strip().split() if args else []
        if not arg_words:
            err_msg = self.i18n.get("widgets.so.usage_error").replace("{user}", user).replace("{trigger}", prefix)
            self.command_service.send_response(err_msg, platform=platform)
            return

        target_user = arg_words[0].lstrip("@").strip()
        reply = self.widget_service.format_shoutout(target_user)
        self.command_service.send_response(reply, platform=platform)

        if self.overlay_server:
            def _fetch_and_trigger():
                avatar_url = self.widget_service.fetch_streamer_avatar(target_user)
                header_text = self.i18n.get("widgets.so.overlay_header")
                target_url = f"https://twitch.tv/{target_user}" if platform == "twitch" else f"https://kick.com/{target_user}"
                self.overlay_server.trigger_widget_event("shoutout", {
                    "target": target_user,
                    "url": target_url,
                    "avatar_url": avatar_url,
                    "header_text": header_text
                })

            threading.Thread(target=_fetch_and_trigger, daemon=True, name=f"ShoutoutAvatar-{target_user}").start()

    def _process_death(self, user: str, args: str, action_word: str = "", platform: str = "kick"):
        arg_clean = args.strip().lower()
        check_target = arg_clean if arg_clean else action_word

        if check_target in _RESET_COMMANDS or action_word in _RESET_COMMANDS:
            new_count = self.widget_service.update_death_count(set_val=0)
            msg = self.i18n.get("widgets.death.msg_reset").replace("{user}", user).replace("{count}", str(new_count))
        elif check_target in _DEATH_SUB_WORDS or action_word.endswith("-") or action_word.endswith("sub"):
            new_count = self.widget_service.update_death_count(delta=-1)
            msg = self.i18n.get("widgets.death.msg_sub").replace("{user}", user).replace("{count}", str(new_count))
        elif check_target in _DEATH_CHECK_WORDS or action_word in _DEATH_CHECK_WORDS:
            new_count = self.widget_service.get_death_count()
            msg = self.i18n.get("widgets.death.msg_check").replace("{user}", user).replace("{count}", str(new_count))
        elif check_target in _DEATH_ADD_WORDS or action_word.endswith("+") or action_word.endswith("add"):
            new_count = self.widget_service.update_death_count(delta=1)
            msg = self.i18n.get("widgets.death.msg_add").replace("{user}", user).replace("{count}", str(new_count))
        else:
            try:
                val = int(check_target)
                new_count = self.widget_service.update_death_count(set_val=max(0, val))
            except ValueError:
                new_count = self.widget_service.update_death_count(delta=1)
            msg = self.i18n.get("widgets.death.msg_add").replace("{user}", user).replace("{count}", str(new_count))

        self.death_count_updated.emit(new_count)
        if self.overlay_server:
            w_death = self.widget_service.get_widget("death")
            title_text = self.i18n.get("widgets.death.overlay_title")
            self.overlay_server.trigger_widget_event("death_update", {
                "count": new_count,
                "is_active": w_death.get("is_active", True),
                "title_text": title_text
            })
        self.command_service.send_response(msg, platform=platform)

    @Slot(str, str, str, object)
    @Slot(str, str, str, object, str, str)
    def handle_chat_message(self, user: str, content: str, color: str = "", badges: list = None, platform: str = "kick", emotes_tag: str = ""):
        if not content or not self.overlay_server:
            return

        emotes_list = []
        for match in self._KICK_EMOTE_REGEX.finditer(content):
            e_id, e_name = match.groups()
            if e_id:
                emotes_list.append({
                    "type": "image",
                    "src": f"https://files.kick.com/emotes/{e_id}/fullsize",
                    "name": e_name
                })
            else:
                emotes_list.append({
                    "type": "text",
                    "src": e_name,
                    "name": e_name
                })

        if platform in ("youtube", "tiktok") and emotes_tag:
            try:
                custom_emotes = json.loads(emotes_tag) if isinstance(emotes_tag, str) and emotes_tag.startswith("[") else []
                for em in custom_emotes:
                    if isinstance(em, dict) and em.get("url"):
                        emotes_list.append({
                            "type": "image",
                            "src": em["url"],
                            "name": em.get("name", f"{platform}_emote")
                        })
            except Exception:
                pass

        if platform == "twitch" and emotes_tag and not emotes_tag.startswith("["):
            for group in emotes_tag.split("/"):
                if ":" in group:
                    e_id = group.split(":")[0]
                    if e_id:
                        emotes_list.append({
                            "type": "image",
                            "src": f"https://static-cdn.jtvnw.net/emoticons/v2/{e_id}/default/dark/2.0",
                            "name": f"twitch_{e_id}"
                        })

        for emoji_char in self._EMOJI_REGEX.findall(content):
            emotes_list.append({
                "type": "text",
                "src": emoji_char,
                "name": emoji_char
            })

        if not emotes_list:
            return

        w_exp = self.widget_service.get_widget("explosion")
        if w_exp.get("is_active", True):
            cfg_exp = w_exp.get("config", {})
            min_emotes = int(cfg_exp.get("min_emotes", 1))
            particle_count = int(cfg_exp.get("particle_count", 15))
            
            if len(emotes_list) >= min_emotes:
                self.overlay_server.trigger_widget_event("emote_explosion", {
                    "emotes": emotes_list,
                    "count": particle_count
                })

        w_combo = self.widget_service.get_widget("combo")
        if w_combo.get("is_active", True):
            cfg_combo = w_combo.get("config", {})
            min_combo = int(cfg_combo.get("min_combo", 3))
            timeout_sec = float(cfg_combo.get("timeout_sec", 5.0))
            now = time.time()

            for emote_obj in emotes_list:
                emote_name = emote_obj["name"]
                if self._last_combo_emote == emote_name and (now - self._last_combo_time) <= timeout_sec:
                    self._combo_count += 1
                else:
                    self._last_combo_emote = emote_name
                    self._combo_count = 1
                self._last_combo_time = now

                if self._combo_count >= min_combo:
                    self.overlay_server.trigger_widget_event("emote_combo", {
                        "emote": emote_name,
                        "src": emote_obj.get("src", ""),
                        "type": emote_obj.get("type", "text"),
                        "count": self._combo_count,
                        "timeout_sec": timeout_sec
                    })

    def _process_explosion_command(self, user: str, args: str, platform: str = "kick"):
        if self.overlay_server:
            sample_emotes = [
                {"type": "text", "src": "🔥", "name": "🔥"},
                {"type": "text", "src": "⚡", "name": "⚡"},
                {"type": "text", "src": "🎉", "name": "🎉"},
                {"type": "text", "src": "🚀", "name": "🚀"}
            ]
            self.overlay_server.trigger_widget_event("emote_explosion", {
                "emotes": sample_emotes,
                "count": 25
            })
            msg = self.i18n.get("widgets.explosion.msg_explosion").replace("{user}", user)
            self.command_service.send_response(msg, platform=platform)

    def _process_combo_command(self, user: str, args: str, platform: str = "kick"):
        if self.overlay_server:
            emote = args.strip() if args.strip() else "KEKW"
            self.overlay_server.trigger_widget_event("emote_combo", {
                "emote": emote,
                "src": "",
                "type": "text",
                "count": 5,
                "timeout_sec": 5.0
            })
            msg = self.i18n.get("widgets.combo.msg_combo").replace("{count}", "5").replace("{emote}", emote)
            self.command_service.send_response(msg, platform=platform)
