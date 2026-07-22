# frontend\views\network_view.py

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget, QHeaderView
from PySide6.QtCore import Qt, Signal, QPointF, QSize, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QFont, QFontMetrics
from frontend.common.utils import get_icon_colored, get_pixmap_colored
from frontend.widgets import BaseView, ModernButton, ModernTableCard
from frontend.common.theme import (
    COLOR_NEUTRAL_200, COLOR_NEUTRAL_500, 
    COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_BLACK, COLOR_BLUE, COLOR_WHITE
)

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
        
        self._blue_col = QColor(COLOR_BLUE)
        self._blue_fill = QColor(self._blue_col)
        self._blue_fill.setAlpha(30)
        
        self._green_col = QColor(COLOR_GREEN)
        self._green_fill = QColor(self._green_col)
        self._green_fill.setAlpha(30)

        self._configs = [
            ("internet", self._blue_col, self._blue_fill),
            ("kick", self._green_col, self._green_fill)
        ]
        
        self._font_small = QFont("Inter", 8)
        self._font_bold = QFont("Inter", 8, QFont.Weight.Bold)
        self._metrics_small = QFontMetrics(self._font_small)
        self._base_tooltip_width = self._metrics_small.horizontalAdvance("Ping / Latency")

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
        all_vals = histories["internet"] + histories["kick"]
        max_val = max(80.0, max(all_vals))
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

        for name, line_color, fill_color in self._configs:
            history = histories[name]
            points = []
            n_points = len(history)
            for i, val in enumerate(history):
                x = left_margin + i * (W / (n_points - 1))
                y = self.height() - bottom_margin - (val / max_scale) * H
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
                
                self._cached_paths.append((name, path, fill_path, line_color, fill_color))

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
                
            painter.setPen(QColor(COLOR_NEUTRAL_200))
            painter.drawText(5, y + 4, val_text)

        painter.setPen(QColor(COLOR_NEUTRAL_200))
        for x, y, text in self._cached_labels:
            painter.drawText(x, y, text)
        for name, path, fill_path, line_color, fill_color in self._cached_paths:
            gradient = QLinearGradient(0, top_margin, 0, self.height() - bottom_margin)
            gradient.setColorAt(0.0, fill_color)
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.fillPath(fill_path, QBrush(gradient))
            
            pen = QPen(line_color, 2.0)
            painter.setPen(pen)
            painter.drawPath(path)

        if self.hovered_idx is not None and self.hovered_idx < 50:
            hover_x = left_margin + self.hovered_idx * (W / 49)
            
            painter.setPen(QPen(QColor(255, 255, 255, 60), 1, Qt.PenStyle.DashLine))
            painter.drawLine(hover_x, top_margin, hover_x, self.height() - bottom_margin)
            
            tooltip_data = []
            histories = self.parent_graph.histories
            max_scale = self._max_scale

            for name, line_color, _ in self._configs:
                val = histories[name][self.hovered_idx]
                y = self.height() - bottom_margin - (val / max_scale) * H
                
                painter.setBrush(QBrush(QColor(line_color.red(), line_color.green(), line_color.blue(), 60)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(hover_x, y), 6, 6)
                
                painter.setBrush(QBrush(line_color))
                painter.drawEllipse(QPointF(hover_x, y), 3, 3)
                
                label = self.parent_graph.i18n.get(f"network.services.{name}")
                tooltip_data.append((label, int(val), line_color))
                
            max_text_w = self._base_tooltip_width
            for label, val, _ in tooltip_data:
                text_w = self._metrics_small.horizontalAdvance(f"{label}: {val} ms")
                if text_w > max_text_w:
                    max_text_w = text_w

            tooltip_w = max_text_w + 35
            tooltip_h = 70
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
            painter.drawText(tooltip_x + 10, tooltip_y + 16, self.parent_graph.i18n.get("network.graph.tooltip_title"))
            
            painter.setFont(self._font_small)
            for i, (label, val, col) in enumerate(tooltip_data):
                y_offset = tooltip_y + 34 + i * 16
                painter.setBrush(QBrush(col))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(tooltip_x + 15, y_offset - 3), 4, 4)
                
                painter.setPen(QColor(COLOR_WHITE))
                painter.drawText(tooltip_x + 25, y_offset, f"{label}: {val} ms")

class LiveNetworkGraph(QFrame):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self.setFixedHeight(295)
        
        self.histories = {
            "internet": [35.0] * 50,
            "kick": [45.0] * 50
        }
        self.current_latencies = {"internet": 35.0, "kick": 45.0}
        self.avg_latencies = {"internet": 35.0, "kick": 45.0}
        self.max_latencies = {"internet": 35.0, "kick": 45.0}
        
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
        self.stats_layout.setSpacing(15)
        
        self.lbl_live = QLabel()
        self.lbl_live.setProperty("role", "caption")
        self.lbl_live.setStyleSheet(f"color: {COLOR_BLUE}; font-weight: bold;")
        
        self.lbl_avg = QLabel()
        self.lbl_avg.setProperty("role", "caption")
        self.lbl_avg.setStyleSheet(f"color: {COLOR_GREEN}; font-weight: bold;")
        
        self.lbl_max = QLabel()
        self.lbl_max.setVisible(False)
        
        self.stats_layout.addWidget(self.lbl_live)
        self.stats_layout.addWidget(self.lbl_avg)
        self.stats_layout.addWidget(self.lbl_max)
        
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.stats_container)
        
        self.main_layout.addLayout(self.header_layout)
        
        self.canvas = GraphCanvas(self)
        self.main_layout.addWidget(self.canvas, stretch=1)
        
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.legend_layout.setSpacing(20)
        
        self.legend_internet = self._create_legend_item(COLOR_BLUE, self.i18n.get("network.services.internet"))
        self.legend_kick = self._create_legend_item(COLOR_GREEN, self.i18n.get("network.services.kick"))
        
        self.legend_layout.addWidget(self.legend_internet)
        self.legend_layout.addWidget(self.legend_kick)
        
        self.main_layout.addLayout(self.legend_layout)
        self._update_labels()

    def _create_legend_item(self, color: str, text: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        lbl_dot = QLabel("● ")
        lbl_dot.setProperty("role", "caption")
        lbl_dot.setStyleSheet(f"color: {color};")
        
        lbl_text = QLabel(text)
        lbl_text.setProperty("role", "caption")
        
        layout.addWidget(lbl_dot)
        layout.addWidget(lbl_text)
        return container
        
    def _update_labels(self):
        int_lbl = self.i18n.get("network.services.internet")
        kick_lbl = self.i18n.get("network.services.kick")
        self.lbl_live.setText(f"{int_lbl}: {int(self.histories['internet'][-1])} ms")
        self.lbl_avg.setText(f"{kick_lbl}: {int(self.histories['kick'][-1])} ms")
        
    def update_graph_data(self, histories: dict, currents: dict, averages: dict, maxima: dict):
        self.histories = histories
        self.current_latencies = currents
        self.avg_latencies = averages
        self.max_latencies = maxima

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
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        h_header = self.table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
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
        layout.setContentsMargins(12, 4, 8, 4)
        layout.setSpacing(10)
        
        lbl_icon = QLabel()
        lbl_icon.setFixedSize(20, 20)
        lbl_icon.setPixmap(get_pixmap_colored(icon_name, COLOR_NEUTRAL_200, size=16))
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold;")
        
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
        lbl_status.setStyleSheet("font-weight: bold;")
        
        layout.addWidget(lbl_status)
        return container, lbl_status

    def _create_latency_cell(self) -> tuple[QWidget, QLabel]:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 4, 12, 4)
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
        
        widgets["status_label"].setText(status_text)
        widgets["status_label"].setStyleSheet(f"color: {color}; font-weight: bold;")
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
