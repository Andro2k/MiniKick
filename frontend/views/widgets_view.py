# frontend\views\widgets_view.py

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QBoxLayout
from frontend.widgets import BaseView, create_two_column_container
from frontend.components.widgets import WidgetCard

class WidgetsView(BaseView):
    widget_saved = Signal(str, bool, str, int, str, object)
    death_count_changed = Signal(int)
    score_changed = Signal(int, int)
    chatters_reset_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n, shoutout_overlay_url: str = "", death_overlay_url: str = "", score_overlay_url: str = "", explosion_overlay_url: str = "", combo_overlay_url: str = "", poll_overlay_url: str = "", pinned_overlay_url: str = "", chatters_overlay_url: str = "", clock_overlay_url: str = "", parent=None):
        super().__init__(i18n=i18n, title_key="widgets.header.title", subtitle_key="widgets.header.subtitle", parent=parent)
        self.cards: dict[str, WidgetCard] = {}
        self._is_compact_layout: bool | None = None
        self.set_overlay_urls(
            shoutout_url=shoutout_overlay_url,
            death_url=death_overlay_url,
            score_url=score_overlay_url,
            explosion_url=explosion_overlay_url,
            combo_url=combo_overlay_url,
            poll_url=poll_overlay_url,
            pinned_url=pinned_overlay_url,
            chatters_url=chatters_overlay_url,
            clock_url=clock_overlay_url,
        )
        self._setup_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()

    def _setup_ui(self):
        self.body_container, self.body_layout, self.columns_layout, self.col1_layout, self.col2_layout = create_two_column_container(self)

        self._add_card("clock", self.i18n.get("widgets.clock.title"), self.i18n.get("widgets.clock.desc"), "clock-filled.svg", column=1, obs_url=self.clock_overlay_url)
        self._add_card("poll", self.i18n.get("widgets.poll.title"), self.i18n.get("widgets.poll.desc"), "clipboard-filled.svg", column=1, obs_url=self.poll_overlay_url)
        self._add_card("chatters", self.i18n.get("widgets.chatters.title"), self.i18n.get("widgets.chatters.desc"), "users-filled.svg", column=1, obs_url=self.chatters_overlay_url)
        self._add_card("shoutout", self.i18n.get("widgets.so.title"), self.i18n.get("widgets.so.desc"), "profile-tick-filled.svg", column=1, obs_url=self.shoutout_overlay_url)
        self._add_card("score", self.i18n.get("widgets.score.title"), self.i18n.get("widgets.score.desc"), "cup-star-filled.svg", column=1, obs_url=self.score_overlay_url)
        self._add_card("pinned", self.i18n.get("widgets.pinned.title"), self.i18n.get("widgets.pinned.desc"), "pin-tack-filled.svg", column=2, obs_url=self.pinned_overlay_url)
        self._add_card("explosion", self.i18n.get("widgets.explosion.title"), self.i18n.get("widgets.explosion.desc"), "emoji-circle-filled.svg", column=2, obs_url=self.explosion_overlay_url)
        self._add_card("death", self.i18n.get("widgets.death.title"), self.i18n.get("widgets.death.desc"), "ghost-filled.svg", column=2, obs_url=self.death_overlay_url)
        self._add_card("combo", self.i18n.get("widgets.combo.title"), self.i18n.get("widgets.combo.desc"), "squares-filled.svg", column=2, obs_url=self.combo_overlay_url)

        self.main_layout.addWidget(self.body_container)
        self.main_layout.addStretch()

    def set_overlay_urls(self, shoutout_url: str = "", death_url: str = "", score_url: str = "", explosion_url: str = "", combo_url: str = "", poll_url: str = "", pinned_url: str = "", chatters_url: str = "", clock_url: str = ""):
        self.shoutout_overlay_url = shoutout_url
        self.death_overlay_url = death_url
        self.score_overlay_url = score_url
        self.explosion_overlay_url = explosion_url
        self.combo_overlay_url = combo_url
        self.poll_overlay_url = poll_url
        self.pinned_overlay_url = pinned_url
        self.chatters_overlay_url = chatters_url
        self.clock_overlay_url = clock_url
        if "pinned" in self.cards and pinned_url:
            self.cards["pinned"].set_obs_overlay_url(pinned_url)
        if "poll" in self.cards and poll_url:
            self.cards["poll"].set_obs_overlay_url(poll_url)
        if "chatters" in self.cards and chatters_url:
            self.cards["chatters"].set_obs_overlay_url(chatters_url)
        if "clock" in self.cards and clock_url:
            self.cards["clock"].set_obs_overlay_url(clock_url)
        if "shoutout" in self.cards and shoutout_url:
            self.cards["shoutout"].set_obs_overlay_url(shoutout_url)
        if "death" in self.cards and death_url:
            self.cards["death"].set_obs_overlay_url(death_url)
        if "score" in self.cards and score_url:
            self.cards["score"].set_obs_overlay_url(score_url)
        if "explosion" in self.cards and explosion_url:
            self.cards["explosion"].set_obs_overlay_url(explosion_url)
        if "combo" in self.cards and combo_url:
            self.cards["combo"].set_obs_overlay_url(combo_url)

    def _add_card(self, w_id: str, title: str, desc: str, icon_name: str, column: int = 1, obs_url: str = ""):
        card = WidgetCard(w_id, title, desc, icon_name, self.i18n, obs_overlay_url=obs_url)
        card.widget_changed.connect(self.widget_saved.emit)
        card.counter_action_triggered.connect(self._handle_counter_action)
        self.cards[w_id] = card

        if column == 1:
            self.col1_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self.col2_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignTop)

    def _handle_counter_action(self, _w_id: str, action: str, data: dict):
        if action == "set_death":
            self.death_count_changed.emit(data.get("count", 0))
        elif action == "set_score":
            self.score_changed.emit(data.get("wins", 0), data.get("losses", 0))
        elif action == "reset_chatters":
            self.chatters_reset_requested.emit()

    def populate_widgets(self, widgets_data: dict):
        self.setUpdatesEnabled(False)
        try:
            for w_id, card in self.cards.items():
                if w_id in widgets_data:
                    card.set_data(widgets_data[w_id])
        finally:
            self.setUpdatesEnabled(True)

    def update_death_count_display(self, count: int):
        if "death" in self.cards:
            self.cards["death"].update_death_count_display(count)

    def update_score_display(self, wins: int, losses: int):
        if "score" in self.cards:
            self.cards["score"].update_score_display(wins, losses)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'columns_layout'):
            is_compact = self.width() < 920
            if self._is_compact_layout != is_compact:
                self._is_compact_layout = is_compact
                if is_compact:
                    self.columns_layout.setDirection(QBoxLayout.Direction.TopToBottom)
                    self.columns_layout.setStretch(0, 0)
                    self.columns_layout.setStretch(1, 0)
                else:
                    self.columns_layout.setDirection(QBoxLayout.Direction.LeftToRight)
                    self.columns_layout.setStretch(0, 1)
                    self.columns_layout.setStretch(1, 1)
