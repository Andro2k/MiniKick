# frontend\views\network_view.py

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget, QHeaderView, QPushButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QPointF, QSize, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QFont, QFontMetrics
)
from frontend.common.utils import get_icon_colored, get_pixmap_colored
from frontend.widgets import BaseView, ModernButton, ModernTableCard
from frontend.common.theme import (
    COLOR_NEUTRAL_200, COLOR_NEUTRAL_400, COLOR_NEUTRAL_500, COLOR_NEUTRAL_800, COLOR_NEUTRAL_850,
    COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_BLACK, COLOR_BLUE, COLOR_PURPLE, COLOR_WHITE
)

_SERVICE_PALETTE = {
    "internet": (COLOR_BLUE, "network.graph.filter_internet"),
    "kick": (COLOR_GREEN, "network.graph.filter_kick"),
    "chat_websocket": (COLOR_PURPLE, "network.graph.filter_chat_websocket"),
    "overlay": (COLOR_AMBER, "network.graph.filter_overlay"),
    "spotify": ("#1DB954", "network.graph.filter_spotify"),
    "youtube": (COLOR_RED, "network.graph.filter_youtube")
}

class GraphCanvas(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_graph = parent
        self.setMouseTracking(True)
        self.hovered_idx = None
        self.mouse_pos = None
        self._dirty = True
        self._cached_paths = []        
        self._cached_grid_lines = []   
        self._cached_labels = []       
        self._max_scale = 80
        self.selected_service = "all"
        
        self._font_small = QFont("Inter", 8)
        self._font_bold = QFont("Inter", 8, QFont.Weight.Bold)
        self._metrics_small = QFontMetrics(self._font_small)
        self._base_tooltip_width = self._metrics_small.horizontalAdvance("Ping / Latency")

    def set_selected_service(self, service_key: str):
        if self.selected_service != service_key:
            self.selected_service = service_key
            self._dirty = True
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._dirty = True

    def mark_dirty(self):
        self._dirty = True

    def mouseMoveEvent(self, event):
        left_margin = 45
        right_margin = 10
        W = self.width() - left_margin - right_margin
        if W > 0:
            x = event.position().x()
            idx = int((x - left_margin) / (W / 49) + 0.5)
            if 0 <= idx < 50:
                if self.hovered_idx != idx:
                    self.hovered_idx = idx
                    self.mouse_pos = event.position()
                    self.update()
                return
        if self.hovered_idx is not None:
            self.hovered_idx = None
            self.mouse_pos = None
            self.update()

    def leaveEvent(self, event):
        if self.hovered_idx is not None:
            self.hovered_idx = None
            self.mouse_pos = None
            self.update()

    def _rebuild_cache(self):
        self._cached_paths.clear()
        self._cached_grid_lines.clear()
        self._cached_labels.clear()

        left_margin = 45
        right_margin = 10
        top_margin = 15
        bottom_margin = 25
        
        W = self.width() - left_margin - right_margin
        H = self.height() - top_margin - bottom_margin
        
        if W <= 0 or H <= 0:
            return
            
        histories = self.parent_graph.histories
        
        if self.selected_service != "all" and self.selected_service in histories:
            active_keys = [self.selected_service]
        else:
            active_keys = [k for k in histories.keys() if k != "overlay"]
            if not active_keys:
                active_keys = list(histories.keys())

        all_vals = []
        for k in active_keys:
            all_vals.extend(histories[k])

        max_val = max(80.0, max(all_vals) if all_vals else 80.0)
        max_scale = ((int(max_val) // 40) + 1) * 40  
        self._max_scale = max_scale
        
        grid_lines = 4
        for i in range(grid_lines + 1):
            val = (max_scale / grid_lines) * i
            y = self.height() - bottom_margin - (val / max_scale) * H
            is_dash = (i > 0 and i < grid_lines)
            self._cached_grid_lines.append((y, f"{int(val)} ms", is_dash))
            
        self._cached_labels.append((left_margin, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_45s")))
        self._cached_labels.append((left_margin + W // 2 - 15, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_20s")))
        self._cached_labels.append((self.width() - right_margin - 30, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_now")))

        for name, history in histories.items():
            if self.selected_service != "all" and name != self.selected_service:
                continue

            color_str, _ = _SERVICE_PALETTE.get(name, (COLOR_GREEN, ""))
            line_color = QColor(color_str)
            fill_color = QColor(line_color)
            fill_color.setAlpha(35 if self.selected_service == name else 18)

            points = []
            n_points = len(history)
            for i, val in enumerate(history):
                x = left_margin + i * (W / (n_points - 1))
                y = self.height() - bottom_margin - (min(val, max_scale) / max_scale) * H
                points.append(QPointF(x, y))
                
            if len(points) >= 2:
                path = QPainterPath()
                path.moveTo(points[0])
                for i in range(1, len(points)):
                    p_prev = points[i-1]
                    p_curr = points[i]
                    dx = p_curr.x() - p_prev.x()
                    cp1 = QPointF(p_prev.x() + dx / 2, p_prev.y())
                    cp2 = QPointF(p_prev.x() + dx / 2, p_curr.y())
                    path.cubicTo(cp1, cp2, p_curr)
                    
                fill_path = QPainterPath(path)
                fill_path.lineTo(points[-1].x(), self.height() - bottom_margin)
                fill_path.lineTo(points[0].x(), self.height() - bottom_margin)
                fill_path.closeSubpath()
                
                line_width = 2.5 if (self.selected_service == name or self.selected_service == "all") else 1.5
                self._cached_paths.append((name, path, fill_path, line_color, fill_color, line_width))

    def paintEvent(self, event):
        if self._dirty:
            self._rebuild_cache()
            self._dirty = False

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        left_margin = 45
        right_margin = 10
        top_margin = 15
        bottom_margin = 25
        
        W = self.width() - left_margin - right_margin
        H = self.height() - top_margin - bottom_margin
        
        if W <= 0 or H <= 0:
            return
            
        painter.setFont(self._font_small)
        
        for y, val_text, is_dash in self._cached_grid_lines:
            if is_dash:
                painter.setPen(QPen(QColor(255, 255, 255, 12), 1, Qt.PenStyle.DashLine))
                painter.drawLine(left_margin, y, self.width() - right_margin, y)
                
            painter.setPen(QColor(COLOR_NEUTRAL_400))
            painter.drawText(5, int(y + 4), val_text)

        painter.setPen(QColor(COLOR_NEUTRAL_400))
        for x, y, text in self._cached_labels:
            painter.drawText(int(x), int(y), text)

        for name, path, fill_path, line_color, fill_color, line_w in self._cached_paths:
            gradient = QLinearGradient(0, top_margin, 0, self.height() - bottom_margin)
            gradient.setColorAt(0.0, fill_color)
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillPath(fill_path, QBrush(gradient))
            
            pen = QPen(line_color, line_w)
            painter.setPen(pen)
            painter.drawPath(path)

        if self.hovered_idx is not None and self.hovered_idx < 50:
            hover_x = left_margin + self.hovered_idx * (W / 49)
            
            painter.setPen(QPen(QColor(255, 255, 255, 60), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(hover_x), top_margin, int(hover_x), self.height() - bottom_margin)
            
            tooltip_data = []
            histories = self.parent_graph.histories
            max_scale = self._max_scale

            active_services = list(histories.keys()) if self.selected_service == "all" else [self.selected_service]

            for name in active_services:
                if name not in histories:
                    continue
                val = histories[name][self.hovered_idx]
                y = self.height() - bottom_margin - (min(val, max_scale) / max_scale) * H
                color_str, label_key = _SERVICE_PALETTE.get(name, (COLOR_GREEN, ""))
                line_color = QColor(color_str)
                
                painter.setBrush(QBrush(QColor(line_color.red(), line_color.green(), line_color.blue(), 60)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(hover_x, y), 5, 5)
                
                painter.setBrush(QBrush(line_color))
                painter.drawEllipse(QPointF(hover_x, y), 3, 3)
                
                label = self.parent_graph.i18n.get(label_key) or name
                tooltip_data.append((label, int(val), line_color))
                
            max_text_w = self._base_tooltip_width
            for label, val, _ in tooltip_data:
                text_w = self._metrics_small.horizontalAdvance(f"{label}: {val} ms")
                if text_w > max_text_w:
                    max_text_w = text_w

            tooltip_w = max_text_w + 35
            tooltip_h = 24 + len(tooltip_data) * 18
            tooltip_x = hover_x + 15
            if tooltip_x + tooltip_w > self.width():
                tooltip_x = hover_x - tooltip_w - 15
            tooltip_y = max(10, self.height() // 2 - tooltip_h // 2)
            
            tooltip_rect = QRectF(tooltip_x, tooltip_y, tooltip_w, tooltip_h)
            painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
            painter.setBrush(QBrush(QColor(15, 15, 15, 230)))
            painter.drawRoundedRect(tooltip_rect, 6, 6)
            
            painter.setFont(self._font_bold)
            painter.setPen(QColor(COLOR_NEUTRAL_200))
            painter.drawText(int(tooltip_x + 10), int(tooltip_y + 16), self.parent_graph.i18n.get("network.graph.tooltip_title"))
            
            painter.setFont(self._font_small)
            for i, (label, val, col) in enumerate(tooltip_data):
                y_offset = tooltip_y + 32 + i * 16
                painter.setBrush(QBrush(col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(tooltip_x + 15, y_offset - 3), 4, 4)
                
                painter.setPen(QColor(COLOR_WHITE))
                painter.drawText(int(tooltip_x + 25), int(y_offset), f"{label}: {val} ms")

class LiveNetworkGraph(QFrame):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self.setFixedHeight(340)
        
        self.histories = {}
        self.current_latencies = {}
        self.avg_latencies = {}
        self.max_latencies = {}
        self.min_latencies = {}
        self.jitter_by_service = {}
        self.stability_by_service = {}

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(10)

        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(12)
        
        self.lbl_title = QLabel(self.i18n.get("network.graph.title"))
        self.lbl_title.setProperty("role", "h3")
        
        self.stats_container = QWidget()
        self.stats_layout = QHBoxLayout(self.stats_container)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(12)
        
        self.lbl_live = QLabel()
        self.lbl_live.setProperty("role", "caption")
        self.lbl_live.setProperty("state", "info")
        
        self.lbl_avg = QLabel()
        self.lbl_avg.setProperty("role", "caption")
        self.lbl_avg.setProperty("state", "success")

        self.lbl_min = QLabel()
        self.lbl_min.setProperty("role", "caption")

        self.lbl_jitter = QLabel()
        self.lbl_jitter.setProperty("role", "caption")

        self.lbl_stability = QLabel()
        self.lbl_stability.setProperty("role", "caption")
        self.lbl_stability.setProperty("state", "bold")

        self.stats_layout.addWidget(self.lbl_live)
        self.stats_layout.addWidget(self.lbl_avg)
        self.stats_layout.addWidget(self.lbl_min)
        self.stats_layout.addWidget(self.lbl_jitter)
        self.stats_layout.addWidget(self.lbl_stability)
        
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.stats_container)
        
        self.main_layout.addLayout(self.header_layout)

        self.filter_container = QWidget()
        self.filter_layout = QHBoxLayout(self.filter_container)
        self.filter_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_layout.setSpacing(6)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.filter_buttons = {}
        filters = [
            ("all", self.i18n.get("network.graph.filter_all")),
            ("internet", self.i18n.get("network.graph.filter_internet")),
            ("kick", self.i18n.get("network.graph.filter_kick")),
            ("chat_websocket", self.i18n.get("network.graph.filter_chat_websocket")),
            ("overlay", self.i18n.get("network.graph.filter_overlay")),
            ("spotify", self.i18n.get("network.graph.filter_spotify")),
            ("youtube", self.i18n.get("network.graph.filter_youtube"))
        ]

        for key, label_text in filters:
            btn = QPushButton(label_text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_NEUTRAL_850};
                    color: {COLOR_NEUTRAL_400};
                    border: 1px solid {COLOR_NEUTRAL_800};
                    border-radius: 6px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_NEUTRAL_800};
                    color: {COLOR_WHITE};
                }}
                QPushButton:checked {{
                    background-color: {COLOR_GREEN};
                    color: {COLOR_BLACK};
                    border-color: {COLOR_GREEN};
                }}
            """)
            if key == "all":
                btn.setChecked(True)

            self.btn_group.addButton(btn)
            self.filter_buttons[key] = btn
            self.filter_layout.addWidget(btn)

            btn.clicked.connect(lambda _, k=key: self._on_filter_changed(k))

        self.filter_layout.addStretch()
        self.main_layout.addWidget(self.filter_container)
        
        self.canvas = GraphCanvas(self)
        self.main_layout.addWidget(self.canvas, stretch=1)
        
        self._update_labels()

    def _on_filter_changed(self, service_key: str):
        self.canvas.set_selected_service(service_key)
        self._update_labels()

    def _update_labels(self):
        selected = self.canvas.selected_service
        live_str = self.i18n.get("network.graph.live")
        avg_str = self.i18n.get("network.graph.avg")
        min_str = self.i18n.get("network.graph.min")
        jitter_str = self.i18n.get("network.graph.jitter")

        if selected == "all":
            int_curr = int(self.current_latencies.get("internet", 0))
            int_avg = int(self.avg_latencies.get("internet", 0))
            int_min = int(self.min_latencies.get("internet", 0))
            int_jit = int(self.jitter_by_service.get("internet", 0))
            stab = self.stability_by_service.get("internet", "good")

            self.lbl_live.setText(f"{live_str}: {int_curr} ms")
            self.lbl_avg.setText(f"{avg_str}: {int_avg} ms")
            self.lbl_min.setText(f"{min_str}: {int_min} ms")
            self.lbl_jitter.setText(f"{jitter_str}: ±{int_jit} ms")
            
            stab_text = self.i18n.get(f"network.graph.stability_{stab}") or stab.capitalize()
            self.lbl_stability.setText(f"● {stab_text}")
        elif selected in self.current_latencies:
            curr = int(self.current_latencies.get(selected, 0))
            avg = int(self.avg_latencies.get(selected, 0))
            mn = int(self.min_latencies.get(selected, 0))
            jit = int(self.jitter_by_service.get(selected, 0))
            stab = self.stability_by_service.get(selected, "good")

            self.lbl_live.setText(f"{live_str}: {curr} ms")
            self.lbl_avg.setText(f"{avg_str}: {avg} ms")
            self.lbl_min.setText(f"{min_str}: {mn} ms")
            self.lbl_jitter.setText(f"{jitter_str}: ±{jit} ms")

            stab_text = self.i18n.get(f"network.graph.stability_{stab}") or stab.capitalize()
            self.lbl_stability.setText(f"● {stab_text}")

    def update_graph_data(
        self, histories: dict, currents: dict, averages: dict, maxima: dict,
        minima: dict = None, jitters: dict = None, stabilities: dict = None
    ):
        self.histories = histories
        self.current_latencies = currents
        self.avg_latencies = averages
        self.max_latencies = maxima
        if minima:
            self.min_latencies = minima
        if jitters:
            self.jitter_by_service = jitters
        if stabilities:
            self.stability_by_service = stabilities

        if self.isVisible():
            self._update_labels()
            self.canvas.mark_dirty()
            self.canvas.update()

class NetworkView(BaseView):
    check_requested = Signal()
    view_shown = Signal()

    _STATUS_CONFIG = {
        "checking": (COLOR_NEUTRAL_500, "checking"),
        "online":   (COLOR_GREEN,       "online"),
        "warning":  (COLOR_AMBER,       "warning"),
    }

    def __init__(self, i18n):
        super().__init__(i18n=i18n, title_key="network.header.title", subtitle_key="network.header.subtitle")
        self.status_widgets = {}
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        self.btn_check = ModernButton(self.i18n.get("network.btn_check"), role="action_accent")
        self.btn_check.setIcon(get_icon_colored("refresh.svg", COLOR_BLACK, 16))
        self.btn_check.setIconSize(QSize(16, 16))
        self.btn_check.setFixedWidth(200)
        self.btn_check.clicked.connect(self.check_requested.emit)
        btn_layout.addWidget(self.btn_check)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addSpacing(10)
        
        self.graph = LiveNetworkGraph(self.i18n, self)
        self.main_layout.addWidget(self.graph)
        self.main_layout.addSpacing(10)
        
        self.service_configs = [
            ("internet", "network.services.internet", "network.services.internet_desc", "wifi.svg"),
            ("chat_websocket", "network.services.chat_websocket", "network.services.chat_websocket_desc", "message.svg"),
            ("overlay", "network.services.overlay", "network.services.overlay_desc", "plug.svg"),
            ("kick", "network.services.kick", "network.services.kick_desc", "kick.svg"),
            ("spotify", "network.services.spotify", "network.services.spotify_desc", "brand-spotify.svg"),
            ("youtube", "network.services.youtube", "network.services.youtube_desc", "brand-youtube.svg")
        ]

        col_service = self.i18n.get("network.table.col_service")
        col_desc = self.i18n.get("network.table.col_desc")
        col_status = self.i18n.get("network.table.col_status")
        col_latency = self.i18n.get("network.table.col_latency")

        self.table_card = ModernTableCard(
            title_text=self.i18n.get("network.table.title"),
            headers=[col_service, col_desc, col_status, col_latency],
            parent=self
        )
        self.table_card.setMinimumHeight(380)
        
        self.table = self.table_card.table
        self.table.setRowCount(len(self.service_configs))
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 110)
        
        for row, config in enumerate(self.service_configs):
            key, title_key, desc_key, icon_name = config
            
            service_widget, lbl_icon = self._create_service_cell(self.i18n.get(title_key), icon_name)
            self.table.setCellWidget(row, 0, service_widget)
            
            desc_widget = self._create_desc_cell(self.i18n.get(desc_key))
            self.table.setCellWidget(row, 1, desc_widget)
            
            status_widget, lbl_status = self._create_status_cell()
            self.table.setCellWidget(row, 2, status_widget)
            
            latency_widget, lbl_latency = self._create_latency_cell()
            self.table.setCellWidget(row, 3, latency_widget)
            
            self.status_widgets[key] = {
                "icon_label": lbl_icon,
                "icon_name": icon_name,
                "status_label": lbl_status,
                "latency_label": lbl_latency
            }
            
        self.main_layout.addWidget(self.table_card)
        self.main_layout.addStretch()

    def _create_service_cell(self, title: str, icon_name: str) -> tuple[QWidget, QLabel]:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)
        
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(20, 20)
        lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_200, size=16))
        
        lbl_title = QLabel(title)
        lbl_title.setProperty("state", "bold")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addStretch()
        return container, lbl_icon

    def _create_desc_cell(self, description: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        
        lbl_desc = QLabel(description)
        lbl_desc.setProperty("role", "body")
        lbl_desc.setWordWrap(True)
        
        layout.addWidget(lbl_desc)
        layout.addStretch()
        return container

    def _create_status_cell(self) -> tuple[QWidget, QLabel]:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_status = QLabel("-")
        lbl_status.setProperty("role", "body")
        lbl_status.setProperty("state", "bold")
        
        layout.addWidget(lbl_status)
        return container, lbl_status

    def _create_latency_cell(self) -> tuple[QWidget, QLabel]:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        lbl_latency = QLabel("-")
        lbl_latency.setProperty("role", "caption")
        
        layout.addWidget(lbl_latency)
        return container, lbl_latency

    def _set_cell_status(self, key: str, status: str, latency: int, status_text: str):
        widgets = self.status_widgets.get(key)
        if not widgets:
            return
            
        color, status_key = self._STATUS_CONFIG.get(status, (COLOR_RED, "offline"))
        latency_text = f"{latency} ms" if status_key != "checking" and latency >= 0 else ("-" if status_key == "offline" else "")
        
        state_map = {"online": "success", "warning": "warning", "offline": "danger", "checking": "info"}
        target_state = state_map.get(status, "danger")
        
        widgets["status_label"].setText(status_text)
        widgets["status_label"].setProperty("state", target_state)
        widgets["status_label"].style().unpolish(widgets["status_label"])
        widgets["status_label"].style().polish(widgets["status_label"])
        
        widgets["latency_label"].setText(latency_text)
        widgets["icon_label"].setPixmap(get_pixmap_colored(widgets["icon_name"], color, size=16))

    def set_checking_state(self):
        self.btn_check.setEnabled(False)
        checking_str = self.i18n.get("network.status.checking")
        for key in self.status_widgets.keys():
            self._set_cell_status(key, "checking", -1, checking_str)

    def update_status(self, results: dict):
        self.btn_check.setEnabled(True)
        for key, info in results.items():
            status = info["status"]
            latency = info["latency"]
            status_text = self.i18n.get(f"network.status.{status}")
            self._set_cell_status(key, status, latency, status_text)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()
