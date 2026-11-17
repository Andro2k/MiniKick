# frontend\views\stats_view.py
"""Vista del módulo de estadísticas del canal."""

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QBoxLayout, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget,
)
from frontend.common import BrandColors, Palette, Size
from frontend.components.stats import ComparisonBarChart, KpiCard, PeakHoursChart, StatsChattersTable
from frontend.views.base_view import BaseView
from frontend.widgets import ModernCard, NoWheelComboBox

logger = logging.getLogger("minikick.views.stats")

_PERIODS = (("today", "stats.period.today"), ("7d", "stats.period.last_7"), ("30d", "stats.period.last_30"))
_PLATFORMS = (
    ("kick", "Kick", BrandColors.GREEN),
    ("twitch", "Twitch", BrandColors.TWITCH),
    ("youtube", "YouTube", BrandColors.RED),
    ("tiktok", "TikTok", BrandColors.TIKTOK),
)


class StatsView(BaseView):
    period_changed = Signal(str)
    chatters_date_changed = Signal(str)
    activate_chatters_requested = Signal()

    def __init__(self, i18n, parent=None):
        super().__init__(i18n=i18n, title_key="stats.header.title", subtitle_key="stats.header.subtitle", parent=parent)
        self._kpi_cols = -1
        self._rendered_top_commands: list[dict] | None = None
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout.setSpacing(Size.SPACING_MD)
        self._setup_toolbar()
        self._setup_kpis()
        self._setup_charts_row()
        self._setup_details_row()
        self.main_layout.addStretch()

    def _caption(self, key: str, role: str = "text_h2") -> QLabel:
        label = QLabel(self.i18n.get(key), self)
        label.setProperty("role", role)
        return label

    def _setup_toolbar(self):
        row = QHBoxLayout()
        row.setSpacing(Size.SPACING_MD)
        row.addWidget(self._caption("stats.toolbar.overview"))
        row.addStretch()
        self.combo_period = NoWheelComboBox(parent=self)
        for period_id, key in _PERIODS:
            self.combo_period.addItem(self.i18n.get(key), period_id)
        self.combo_period.currentIndexChanged.connect(self._on_period_index_changed)
        row.addWidget(self.combo_period)
        self.main_layout.addLayout(row)

    def _setup_kpis(self):
        vs_text = self.i18n.get("stats.kpi.vs_previous")
        specs = (
            ("messages", "stats.kpi.messages", "messages-square.svg", True),
            ("commands", "stats.kpi.commands", "command.svg", True),
            ("redemptions", "stats.kpi.redemptions", "package-open.svg", True),
            ("spam", "stats.kpi.spam", "shield.svg", False),
        )
        self.kpi_cards = {key: KpiCard(self.i18n.get(title), icon, vs_text, better, self)
                          for key, title, icon, better in specs}
        container = QWidget(self)
        self.kpi_grid = QGridLayout(container)
        self.kpi_grid.setContentsMargins(*Size.Margin.MRG_NON)
        self.kpi_grid.setSpacing(Size.SPACING_MD)
        self._relayout_kpis(4)
        self.main_layout.addWidget(container)

    def _relayout_kpis(self, cols: int):
        if cols == self._kpi_cols:
            return
        self._kpi_cols = cols
        for i, card in enumerate(self.kpi_cards.values()):
            self.kpi_grid.addWidget(card, i // cols, i % cols)

    def _setup_charts_row(self):
        self.charts_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.charts_layout.setSpacing(Size.SPACING_MD)

        self.chart_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.lbl_chart_title = self._caption("stats.chart.title_hourly")
        self.lbl_chart_legend = QLabel(self)
        self.lbl_chart_legend.setProperty("role", "text_caption")
        self.chart = ComparisonBarChart(self)
        self.chart_card.addWidget(self.lbl_chart_title)
        self.chart_card.addWidget(self.lbl_chart_legend)
        self.chart_card.addWidget(self.chart, 1)
        self.charts_layout.addWidget(self.chart_card, stretch=3)

        side = QWidget(self)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(*Size.Margin.MRG_NON)
        side_layout.setSpacing(Size.SPACING_MD)

        self.platforms_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.platforms_card.addWidget(self._caption("stats.platforms.title"))
        self.platform_bars: dict[str, tuple[QProgressBar, QLabel]] = {}
        for platform_id, name, color in _PLATFORMS:
            row = QHBoxLayout()
            row.setSpacing(Size.SPACING_MD)
            lbl_name = QLabel(name, self)
            lbl_name.setProperty("role", "text_body")
            lbl_name.setMinimumWidth(64)
            bar = QProgressBar(self)
            bar.setProperty("role", "top_command_progress")
            bar.setTextVisible(False)
            bar.setRange(0, 100)
            lbl_value = QLabel("0", self)
            lbl_value.setProperty("role", "text_caption")
            lbl_value.setMinimumWidth(96)
            lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl_name)
            row.addWidget(bar, stretch=1)
            row.addWidget(lbl_value)
            self.platforms_card.addLayout(row)
            self.platform_bars[platform_id] = (bar, lbl_value)
        side_layout.addWidget(self.platforms_card)

        self.peak_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.peak_card.addWidget(self._caption("stats.peak.title"))
        self.lbl_peak = QLabel(self)
        self.lbl_peak.setProperty("role", "text_body")
        self.peak_chart = PeakHoursChart(self)
        self.peak_card.addWidget(self.lbl_peak)
        self.peak_card.addWidget(self.peak_chart, 1)
        side_layout.addWidget(self.peak_card, stretch=1)

        self.charts_layout.addWidget(side, stretch=2)
        self.main_layout.addLayout(self.charts_layout)

    def _setup_details_row(self):
        self.details_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.details_layout.setSpacing(Size.SPACING_MD)

        self.chatters_table = StatsChattersTable(self.i18n, parent=self)
        self.chatters_table.date_selected.connect(self.chatters_date_changed.emit)
        self.chatters_table.activate_widget_requested.connect(self.activate_chatters_requested.emit)
        self.details_layout.addWidget(self.chatters_table, stretch=3)

        side = QWidget(self)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(*Size.Margin.MRG_NON)
        side_layout.setSpacing(Size.SPACING_MD)

        self.top_commands_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.top_commands_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.top_commands_card.addWidget(self._caption("dashboard.analytics.top_commands_title"))
        self.top_commands_container = QVBoxLayout()
        self.top_commands_container.setSpacing(Size.SPACING_SM)
        self.top_commands_card.addLayout(self.top_commands_container)
        side_layout.addWidget(self.top_commands_card)

        self.modules_card = ModernCard(parent=self, margin=Size.Margin.MRG_MED, spacing=Size.SPACING_SM)
        self.modules_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.modules_card.addWidget(self._caption("dashboard.analytics.modules_summary_title"))
        modules_grid = QGridLayout()
        modules_grid.setSpacing(Size.SPACING_SM)
        self.module_values: dict[str, QLabel] = {}
        for col, (key, title_key) in enumerate((
            ("active_commands", "dashboard.analytics.active_commands"),
            ("active_timers", "dashboard.analytics.active_timers"),
            ("total_rewards", "dashboard.analytics.active_rewards"),
        )):
            value = QLabel("0", self)
            value.setProperty("role", "text_h1")
            modules_grid.addWidget(value, 0, col)
            modules_grid.addWidget(self._caption(title_key, "text_caption"), 1, col)
            self.module_values[key] = value
        self.modules_card.addLayout(modules_grid)
        side_layout.addWidget(self.modules_card)

        self.details_layout.addWidget(side, stretch=2)
        self.main_layout.addLayout(self.details_layout)

    def _on_period_index_changed(self, index: int):
        period = self.combo_period.itemData(index)
        if period:
            self.period_changed.emit(period)

    def render_snapshot(self, snapshot) -> None:
        for key, card in self.kpi_cards.items():
            card.set_values(*snapshot.kpis[key])

        key_suffix = "hourly" if snapshot.is_hourly else "daily"
        self.lbl_chart_title.setText(self.i18n.get(f"stats.chart.title_{key_suffix}"))
        cur_name = self.i18n.get("stats.chart.current_today" if snapshot.is_hourly else "stats.chart.current_period")
        prev_name = self.i18n.get("stats.chart.previous_today" if snapshot.is_hourly else "stats.chart.previous_period")
        self.lbl_chart_legend.setText(
            f'<span style="color:{BrandColors.GREEN}">●</span> {cur_name} &nbsp;&nbsp; '
            f'<span style="color:{Palette.NEUTRAL_700}">●</span> {prev_name}'
        )
        self.chart.set_data(snapshot.labels, snapshot.current_series, snapshot.previous_series, cur_name, prev_name)

        self._render_platforms(snapshot.platform_messages)
        self.peak_chart.set_data(snapshot.hourly_totals, snapshot.peak_hour)
        if snapshot.peak_hour is None:
            self.lbl_peak.setText(self.i18n.get("stats.peak.empty"))
        else:
            hour = snapshot.peak_hour
            self.lbl_peak.setText(self.i18n.get("stats.peak.summary").format(
                hours=f"{hour:02d}:00 – {(hour + 1) % 24:02d}:00", pct=f"{snapshot.peak_share:.0f}"))

        self._render_top_commands(snapshot.top_commands)
        for key, label in self.module_values.items():
            label.setText(str(snapshot.modules.get(key, 0)))

    def _render_platforms(self, platform_messages: dict[str, int]):
        total = sum(platform_messages.values())
        for platform_id, (bar, label) in self.platform_bars.items():
            count = platform_messages.get(platform_id, 0)
            pct = (count / total * 100) if total else 0.0
            bar.setValue(round(pct))
            label.setText(f"{count:,}  ·  {pct:.1f}%")

    def _render_top_commands(self, top_commands: list[dict]):
        if self._rendered_top_commands == top_commands:
            return
        self._rendered_top_commands = list(top_commands)
        while self.top_commands_container.count():
            item = self.top_commands_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        if not top_commands:
            self.top_commands_container.addWidget(self._caption("dashboard.analytics.no_commands_used", "text_body"))
            return
        max_count = max(cmd["count"] for cmd in top_commands)
        usages = self.i18n.get("dashboard.analytics.usages")
        for idx, cmd in enumerate(top_commands):
            row = QHBoxLayout()
            row.setSpacing(Size.SPACING_MD)
            lbl_rank = QLabel(f"#{idx + 1}", self)
            lbl_rank.setProperty("role", "rank_number")
            lbl_trigger = QLabel(cmd["trigger"], self)
            lbl_trigger.setProperty("role", "text_body")
            bar = QProgressBar(self)
            bar.setProperty("role", "top_command_progress")
            bar.setTextVisible(False)
            bar.setRange(0, max_count)
            bar.setValue(cmd["count"])
            lbl_count = QLabel(f"{cmd['count']} {usages}", self)
            lbl_count.setProperty("role", "text_caption")
            for widget, stretch in ((lbl_rank, 0), (lbl_trigger, 0), (bar, 1), (lbl_count, 0)):
                row.addWidget(widget, stretch)
            self.top_commands_container.addLayout(row)

    def render_top_chatters(self, chatters: list[dict], total_messages: int = 0):
        self.chatters_table.set_chatters(chatters, total_messages=total_messages)

    def populate_chatter_dates(self, dates: list[str]):
        self.chatters_table.populate_available_dates(dates)

    def set_chatters_widget_active(self, is_active: bool):
        self.chatters_table.set_widget_active(is_active)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = self.width()
        self._relayout_kpis(1 if width < 650 else (2 if width < 950 else 4))
        direction = QBoxLayout.Direction.TopToBottom if width < 1000 else QBoxLayout.Direction.LeftToRight
        for layout in (self.charts_layout, self.details_layout):
            if layout.direction() != direction:
                layout.setDirection(direction)
