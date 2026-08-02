# frontend\components\widgets\widget_card_component.py

from frontend.widgets import ModernDivider
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (QFrame, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QSpinBox, QPushButton, QApplication)
from frontend.common.utils import get_pixmap_colored, get_icon_colored
from frontend.common.theme import COLOR_NEUTRAL_400
from frontend.widgets.controls import ModernSwitch

class WidgetCard(QFrame):
    widget_changed = Signal(str, bool, str, int, str, dict)
    counter_action_triggered = Signal(str, str, dict)

    def __init__(self, widget_id: str, title: str, desc: str, icon_name: str, i18n, obs_overlay_url: str = "", parent=None):
        super().__init__(parent)
        self.widget_id = widget_id
        self.i18n = i18n
        self.obs_overlay_url = obs_overlay_url
        self._is_loading = True
        self._config_data = {}
        self._command = ""
        self._cooldown = 3
        self._permission = "everyone"

        self.setProperty("role", "card")
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._icon_up = get_icon_colored("chevron-up.svg", COLOR_NEUTRAL_400, 20)
        self._icon_down = get_icon_colored("chevron-down.svg", COLOR_NEUTRAL_400, 20)

        self._build_header(title, desc, icon_name)
        self._build_body()

        self.body_widget.hide()
        self._is_loading = False

    def _build_header(self, title: str, desc: str, icon_name: str):
        self.header_widget = QWidget()
        self.header_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        h_layout = QHBoxLayout(self.header_widget)
        h_layout.setContentsMargins(14, 14, 14, 14)
        h_layout.setSpacing(10)

        lbl_icon = QLabel()
        lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_400, 24))
        h_layout.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setProperty("role", "h3")
        
        lbl_desc = QLabel(desc)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)

        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)

        h_layout.addLayout(text_layout, stretch=1)

        self.switch_enable = ModernSwitch()
        self.switch_enable.toggled.connect(self._on_changed)
        h_layout.addWidget(self.switch_enable, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.btn_expand = QPushButton()
        self.btn_expand.setIcon(self._icon_down)
        self.btn_expand.setIconSize(QSize(20, 20))
        self.btn_expand.setFixedSize(30, 30)
        self.btn_expand.setProperty("role", "btn_ghost")
        self.btn_expand.clicked.connect(self.toggle_expand)
        h_layout.addWidget(self.btn_expand, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.main_layout.addWidget(self.header_widget)

    def toggle_expand(self):
        if self.body_widget.isVisible():
            self.body_widget.hide()
            self.btn_expand.setIcon(self._icon_down)
        else:
            self.body_widget.show()
            self.btn_expand.setIcon(self._icon_up)

    def set_obs_overlay_url(self, url: str):
        self.obs_overlay_url = url

    def _copy_obs_url(self):
        if self.obs_overlay_url:
            QApplication.clipboard().setText(self.obs_overlay_url)

    def _build_body(self):
        self.body_widget = QWidget()
        b_layout = QVBoxLayout(self.body_widget)
        b_layout.setContentsMargins(14, 10, 14, 14)
        b_layout.setSpacing(12)

        b_layout.addWidget(ModernDivider())

        self.specific_container = QWidget()
        self.specific_layout = QVBoxLayout(self.specific_container)
        self.specific_layout.setContentsMargins(0, 0, 0, 0)
        self.specific_layout.setSpacing(10)

        if self.widget_id == "shoutout":
            lbl_tpl = QLabel(self.i18n.get("widgets.so.template_label"))
            lbl_tpl.setProperty("role", "body")
            self.txt_template = QLineEdit()
            self.txt_template.textChanged.connect(self._on_changed)
            self.specific_layout.addWidget(lbl_tpl)
            self.specific_layout.addWidget(self.txt_template)

        elif self.widget_id == "death":
            row = QHBoxLayout()
            lbl_count = QLabel(self.i18n.get("widgets.death.count_label"))
            lbl_count.setProperty("role", "body")
            
            self.spn_deaths = QSpinBox()
            self.spn_deaths.setRange(0, 99999)
            self.spn_deaths.valueChanged.connect(self._on_death_counter_changed)

            btn_reset = QPushButton(self.i18n.get("widgets.death.reset_btn"))
            btn_reset.setProperty("role", "action_neutral_border")
            btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reset.clicked.connect(lambda: self.spn_deaths.setValue(0))

            row.addWidget(lbl_count)
            row.addWidget(self.spn_deaths)
            row.addWidget(btn_reset)
            row.addStretch()
            self.specific_layout.addLayout(row)

        elif self.widget_id == "score":
            row = QHBoxLayout()
            lbl_w = QLabel(self.i18n.get("widgets.score.wins_label"))
            lbl_w.setProperty("role", "body")
            self.spn_wins = QSpinBox()
            self.spn_wins.setRange(0, 9999)
            self.spn_wins.valueChanged.connect(self._on_score_counter_changed)

            lbl_l = QLabel(self.i18n.get("widgets.score.losses_label"))
            lbl_l.setProperty("role", "body")
            self.spn_losses = QSpinBox()
            self.spn_losses.setRange(0, 9999)
            self.spn_losses.valueChanged.connect(self._on_score_counter_changed)

            btn_reset = QPushButton(self.i18n.get("widgets.score.reset_btn"))
            btn_reset.setProperty("role", "action_neutral_border")
            btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_reset.clicked.connect(self._reset_score_counters)

            row.addWidget(lbl_w)
            row.addWidget(self.spn_wins)
            row.addWidget(lbl_l)
            row.addWidget(self.spn_losses)
            row.addWidget(btn_reset)
            row.addStretch()
            self.specific_layout.addLayout(row)

        if self.obs_overlay_url:
            obs_row = QHBoxLayout()
            lbl_obs = QLabel(self.i18n.get("widgets.obs_label"))
            lbl_obs.setProperty("role", "body")

            btn_copy_obs = QPushButton(self.i18n.get("widgets.obs_copy_btn"))
            btn_copy_obs.setProperty("role", "action_neutral_border")
            btn_copy_obs.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_copy_obs.clicked.connect(self._copy_obs_url)

            obs_row.addWidget(lbl_obs)
            obs_row.addWidget(btn_copy_obs)
            obs_row.addStretch()
            self.specific_layout.addLayout(obs_row)

        b_layout.addWidget(self.specific_container)
        self.main_layout.addWidget(self.body_widget)

    def set_data(self, data: dict):
        self._is_loading = True
        self.switch_enable.blockSignals(True)
        self.switch_enable.setChecked(data.get("is_active", True))
        self.switch_enable.blockSignals(False)

        self._command = data.get("command", "")
        self._cooldown = data.get("cooldown", 3)
        self._permission = data.get("permission", "everyone")

        cfg = data.get("config", {})
        self._config_data = dict(cfg)

        if self.widget_id == "shoutout" and hasattr(self, "txt_template"):
            self.txt_template.blockSignals(True)
            self.txt_template.setText(cfg.get("template", self.i18n.get("widgets.so.default_msg")))
            self.txt_template.blockSignals(False)
        elif self.widget_id == "death" and hasattr(self, "spn_deaths"):
            self.spn_deaths.blockSignals(True)
            self.spn_deaths.setValue(int(cfg.get("count", 0)))
            self.spn_deaths.blockSignals(False)
        elif self.widget_id == "score" and hasattr(self, "spn_wins"):
            self.spn_wins.blockSignals(True)
            self.spn_losses.blockSignals(True)
            self.spn_wins.setValue(int(cfg.get("wins", 0)))
            self.spn_losses.setValue(int(cfg.get("losses", 0)))
            self.spn_wins.blockSignals(False)
            self.spn_losses.blockSignals(False)

        self._is_loading = False

    def update_death_count_display(self, count: int):
        if hasattr(self, "spn_deaths"):
            self._is_loading = True
            self.spn_deaths.blockSignals(True)
            self.spn_deaths.setValue(count)
            self.spn_deaths.blockSignals(False)
            self._config_data["count"] = count
            self._is_loading = False

    def update_score_display(self, wins: int, losses: int):
        if hasattr(self, "spn_wins"):
            self._is_loading = True
            self.spn_wins.blockSignals(True)
            self.spn_losses.blockSignals(True)
            self.spn_wins.setValue(wins)
            self.spn_losses.setValue(losses)
            self.spn_wins.blockSignals(False)
            self.spn_losses.blockSignals(False)
            self._config_data["wins"] = wins
            self._config_data["losses"] = losses
            self._is_loading = False

    def _on_changed(self):
        if self._is_loading:
            return

        is_active = self.switch_enable.isChecked()

        if self.widget_id == "shoutout" and hasattr(self, "txt_template"):
            self._config_data["template"] = self.txt_template.text()

        self.widget_changed.emit(self.widget_id, is_active, self._command, self._cooldown, self._permission, self._config_data)

    def _on_death_counter_changed(self, val: int):
        if self._is_loading:
            return
        self._config_data["count"] = val
        self.counter_action_triggered.emit(self.widget_id, "set_death", {"count": val})
        self._on_changed()

    def _on_score_counter_changed(self):
        if self._is_loading:
            return
        w_val = self.spn_wins.value()
        l_val = self.spn_losses.value()
        self._config_data["wins"] = w_val
        self._config_data["losses"] = l_val
        self.counter_action_triggered.emit(self.widget_id, "set_score", {"wins": w_val, "losses": l_val})
        self._on_changed()

    def _reset_score_counters(self):
        self.spn_wins.setValue(0)
        self.spn_losses.setValue(0)
