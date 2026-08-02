# frontend\components\music\stats_panel.py

from PySide6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal
from frontend.common.theme import COLOR_NEUTRAL_200
from frontend.common.utils import get_pixmap_colored
from frontend.widgets import ModernCard, ModernSwitch

class MusicStatsPanel(QWidget):
    service_toggled = Signal(bool)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._current_cols = -1
        self._cached_queue_count = None
        self._cached_duration_str = None
        self._cached_service_enabled = None
        self._setup_ui()

    def _setup_ui(self):
        self.stats_grid = QGridLayout(self)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)
        self.stats_grid.setSpacing(12)

        self.card_stat_queue = ModernCard(margin=12, spacing=6)
        
        queue_header = QHBoxLayout()
        icon_queue = QLabel()
        icon_queue.setPixmap(get_pixmap_colored("music.svg", COLOR_NEUTRAL_200, 18))
        lbl_queue_title = QLabel(self.i18n.get("music.stats.queue_title"))
        lbl_queue_title.setProperty("role", "h3")
        queue_header.addWidget(icon_queue)
        queue_header.addWidget(lbl_queue_title)
        queue_header.addStretch()

        self.lbl_stat_queue_count = QLabel("0")
        self.lbl_stat_queue_count.setProperty("role", "h2")
        
        lbl_queue_desc = QLabel(self.i18n.get("music.stats.queue_desc"))
        lbl_queue_desc.setProperty("role", "body")
        lbl_queue_desc.setWordWrap(True)

        self.card_stat_queue.addLayout(queue_header)
        self.card_stat_queue.addWidget(self.lbl_stat_queue_count)
        self.card_stat_queue.addWidget(lbl_queue_desc)

        self.card_stat_duration = ModernCard(margin=12, spacing=6)

        dur_header = QHBoxLayout()
        icon_dur = QLabel()
        icon_dur.setPixmap(get_pixmap_colored("clock.svg", COLOR_NEUTRAL_200, 18))
        lbl_dur_title = QLabel(self.i18n.get("music.stats.duration_title"))
        lbl_dur_title.setProperty("role", "h3")
        dur_header.addWidget(icon_dur)
        dur_header.addWidget(lbl_dur_title)
        dur_header.addStretch()

        self.lbl_stat_duration_sum = QLabel("00:00:00")
        self.lbl_stat_duration_sum.setProperty("role", "h2")
        
        lbl_dur_desc = QLabel(self.i18n.get("music.stats.duration_desc"))
        lbl_dur_desc.setProperty("role", "body")
        lbl_dur_desc.setWordWrap(True)

        self.card_stat_duration.addLayout(dur_header)
        self.card_stat_duration.addWidget(self.lbl_stat_duration_sum)
        self.card_stat_duration.addWidget(lbl_dur_desc)

        self.card_stat_service = ModernCard(margin=12, spacing=6)

        service_header = QHBoxLayout()
        icon_cmd = QLabel()
        icon_cmd.setPixmap(get_pixmap_colored("code.svg", COLOR_NEUTRAL_200, 18))
        lbl_cmd_title = QLabel(self.i18n.get("music.stats.cmd_title"))
        lbl_cmd_title.setProperty("role", "h3")
        
        self.badge_service_container = QFrame()
        self.badge_service_container.setProperty("role", "badge")
        self.badge_service_container.setProperty("state", "everyone")
        badge_layout = QHBoxLayout(self.badge_service_container)
        badge_layout.setContentsMargins(6, 2, 6, 2)
        self.lbl_service_badge = QLabel(self.i18n.get("music.stats.badge_active"))
        badge_layout.addWidget(self.lbl_service_badge)

        self.sw_music_service = ModernSwitch()
        self.sw_music_service.setChecked(True)
        self.sw_music_service.toggled.connect(self._on_service_switch_toggled)

        service_header.addWidget(icon_cmd)
        service_header.addWidget(lbl_cmd_title)
        service_header.addStretch()
        service_header.addWidget(self.badge_service_container)
        service_header.addWidget(self.sw_music_service)

        self.lbl_stat_service_value = QLabel(self.i18n.get("music.stats.service_active"))
        self.lbl_stat_service_value.setProperty("role", "h2")
        
        lbl_cmd_desc = QLabel(self.i18n.get("music.stats.cmd_desc"))
        lbl_cmd_desc.setProperty("role", "body")
        lbl_cmd_desc.setWordWrap(True)

        self.card_stat_service.addLayout(service_header)
        self.card_stat_service.addWidget(self.lbl_stat_service_value)
        self.card_stat_service.addWidget(lbl_cmd_desc)

        self.relayout(1200)

    def relayout(self, width: int):
        cols = 1 if width < 650 else (2 if width < 950 else 3)
        if cols != self._current_cols:
            self._current_cols = cols
            cards = [self.card_stat_queue, self.card_stat_duration, self.card_stat_service]
            for i, card in enumerate(cards):
                row = i // cols
                col = i % cols
                if cols == 2 and i == 2:
                    self.stats_grid.addWidget(card, row, 0, 1, 2)
                else:
                    self.stats_grid.addWidget(card, row, col)

    def _on_service_switch_toggled(self, checked: bool):
        self.update_service_visual_state(checked)
        self.service_toggled.emit(checked)

    def update_service_visual_state(self, enabled: bool):
        if self._cached_service_enabled == enabled:
            return
        self._cached_service_enabled = enabled

        if enabled:
            self.lbl_service_badge.setText(self.i18n.get("music.stats.badge_active"))
            self.badge_service_container.setProperty("state", "everyone")
            self.lbl_stat_service_value.setText(self.i18n.get("music.stats.service_active"))
            self.lbl_stat_service_value.setProperty("state", "normal")
        else:
            self.lbl_service_badge.setText(self.i18n.get("music.stats.badge_disabled"))
            self.badge_service_container.setProperty("state", "broadcaster")
            self.lbl_stat_service_value.setText(self.i18n.get("music.stats.service_disabled"))
            self.lbl_stat_service_value.setProperty("state", "error")

        self.badge_service_container.style().unpolish(self.badge_service_container)
        self.badge_service_container.style().polish(self.badge_service_container)
        self.lbl_service_badge.style().unpolish(self.lbl_service_badge)
        self.lbl_service_badge.style().polish(self.lbl_service_badge)
        self.lbl_stat_service_value.style().unpolish(self.lbl_stat_service_value)
        self.lbl_stat_service_value.style().polish(self.lbl_stat_service_value)

    def set_stats(self, queue_count: int, duration_str: str):
        if self._cached_queue_count == queue_count and self._cached_duration_str == duration_str:
            return
        self._cached_queue_count = queue_count
        self._cached_duration_str = duration_str
        self.lbl_stat_queue_count.setText(str(queue_count))
        self.lbl_stat_duration_sum.setText(duration_str)

    def set_service_state(self, enabled: bool):
        self.sw_music_service.blockSignals(True)
        self.sw_music_service.setChecked(enabled)
        self.sw_music_service.blockSignals(False)
        self.update_service_visual_state(enabled)
