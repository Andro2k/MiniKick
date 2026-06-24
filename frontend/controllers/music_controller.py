# frontend\controllers\music_controller.py

from PySide6.QtCore import QObject, Slot, QTimer
from frontend.workers.music_auth_worker import SpotifyAuthWorker
from backend.providers.spotify.spotify_client import SpotifyMusicProvider

class MusicController(QObject):
    def __init__(self, view, spotify_auth, command_service, toast_manager, i18n):
        super().__init__()
        self.view = view
        self.spotify_auth = spotify_auth
        self.command_service = command_service
        self.toast = toast_manager
        self.i18n = i18n

        self.music_provider = None
        self.auth_worker = None

        self.polling_timer = QTimer(self)
        self.polling_timer.setInterval(5000)
        self.polling_timer.timeout.connect(self._poll_now_playing)

        self._connect_signals()
        self._load_initial_state()

    def _connect_signals(self):
        self.view.connect_requested.connect(self.handle_connect_request)
        self.view.disconnect_requested.connect(self.handle_disconnect_request)
        self.view.command_toggled.connect(self.handle_command_toggle)

    def _load_initial_state(self):
        saved_cmds = {c["trigger"]: c["is_active"] for c in self.command_service.storage.load_all()}
        self.view.blockSignals(True)
        self.view.sw_sr.setChecked(saved_cmds.get("!sr", False))
        self.view.sw_skip.setChecked(saved_cmds.get("!skip", False))
        self.view.sw_song.setChecked(saved_cmds.get("!song", False))
        self.view.blockSignals(False)

        if self.spotify_auth.get_access_token():
            self._init_session_success("music.status.session_remembered")

    @Slot()
    def handle_connect_request(self):
        self.view.btn_connect.setEnabled(False)
        self.view.lbl_auth_status.setText(self.i18n.get("music.status.connecting"))

        self.auth_worker = SpotifyAuthWorker(self.i18n, self.spotify_auth)
        self.auth_worker.auth_success.connect(lambda tokens: self._init_session_success("music.status.connected_user"))
        self.auth_worker.auth_error.connect(self._handle_auth_error)
        self.auth_worker.start()

    def _init_session_success(self, label_key: str):
        self.music_provider = SpotifyMusicProvider(self.spotify_auth, self.i18n)
        self.view.set_auth_state(connected=True, label_key=label_key)
        self.toast.show_toast(self.i18n.get("music.toast.title_spotify"), self.i18n.get("music.toast.connected"), "success")
        
        self.polling_timer.start()
        self._poll_now_playing()

    @Slot(str)
    def _handle_auth_error(self, err_msg: str):
        self.toast.show_toast(self.i18n.get("music.toast.title_spotify"), err_msg, "danger")
        self.view.set_auth_state(connected=False)
        self.view.btn_connect.setEnabled(True)

    @Slot()
    def handle_disconnect_request(self):
        self.polling_timer.stop()
        self.spotify_auth.logout()
        self.music_provider = None
        self.view.set_auth_state(connected=False)
        self.view.update_current_song(None)
        self.toast.show_toast(self.i18n.get("music.toast.title_spotify"), self.i18n.get("music.toast.disconnected"), "info")

    @Slot()
    def _poll_now_playing(self):
        if not self.music_provider:
            return
        song = self.music_provider.get_current_song()
        self.view.update_current_song(song)

    @Slot(str, bool)
    def handle_command_toggle(self, trigger: str, is_active: bool):
        plugin_tags = {
            "!sr": "[PLUGIN_SPOTIFY_SR]",
            "!skip": "[PLUGIN_SPOTIFY_SKIP]",
            "!song": "[PLUGIN_SPOTIFY_SONG]"
        }
        existing = next((c for c in self.command_service.storage.load_all() if c["trigger"] == trigger), None)

        cooldown = existing["cooldown"] if existing else 5
        aliases = existing["aliases"] if existing else ""
        is_regex = existing["is_regex"] if existing else False
        permission = existing["permission"] if existing else ("everyone" if trigger in ("!sr", "!song") else "moderator")

        self.command_service.storage.save_command(
            trigger=trigger,
            response=plugin_tags.get(trigger, "[PLUGIN_SPOTIFY_SR]"),
            is_active=is_active,
            cooldown=cooldown,
            aliases=aliases,
            is_regex=is_regex,
            permission=permission
        )

        status_title = self.i18n.get("command.status.enabled") if is_active else self.i18n.get("command.status.disabled")
        status_msg = self.i18n.get("command.status.toggled_msg").replace("{trigger}", trigger)
        state_color = "success" if is_active else "warning"
        self.toast.show_toast(status_title, status_msg, state_color)