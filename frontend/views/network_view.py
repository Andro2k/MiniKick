# frontend\views\network_view.py

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget
from PySide6.QtCore import Qt, Signal, QPointF, QSize, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QFont, QFontMetrics
from frontend.common.utils import get_icon_colored
from frontend.widgets import BaseView, ModernButton, FlowLayout
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

        blue_col = QColor(COLOR_BLUE)
        blue_fill = QColor(blue_col)
        blue_fill.setAlpha(30)
        
        green_col = QColor(COLOR_GREEN)
        green_fill = QColor(green_col)
        green_fill.setAlpha(30)

        self._configs = [
            ("internet", blue_col, blue_fill),
            ("kick", green_col, green_fill)
        ]

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
                self.hovered_idx = idx
                self.mouse_pos = event.position()
                self.update()
                return
        self.hovered_idx = None
        self.mouse_pos = None
        self.update()

    def leaveEvent(self, event):
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
            
        painter.setFont(QFont("Inter", 8))
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
                
            font = QFont("Inter", 8)
            fm = QFontMetrics(font)
            max_text_w = fm.horizontalAdvance("Ping / Latency")
            for label, val, _ in tooltip_data:
                text_w = fm.horizontalAdvance(f"{label}: {val} ms")
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
            
            painter.setFont(QFont("Inter", 8, QFont.Weight.Bold))
            painter.setPen(QColor(COLOR_NEUTRAL_200))
            painter.drawText(tooltip_x + 10, tooltip_y + 16, "Ping / Latency")
            
            painter.setFont(QFont("Inter", 8))
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
        
        self.legend_internet = QWidget()
        lbl_dot_int = QLabel("● ")
        lbl_dot_int.setProperty("role", "caption")
        lbl_dot_int.setStyleSheet(f"color: {COLOR_BLUE};")
        lbl_txt_int = QLabel(self.i18n.get("network.services.internet"))
        lbl_txt_int.setProperty("role", "caption")
        lay_int = QHBoxLayout(self.legend_internet)
        lay_int.setContentsMargins(0, 0, 0, 0)
        lay_int.setSpacing(2)
        lay_int.addWidget(lbl_dot_int)
        lay_int.addWidget(lbl_txt_int)
        
        self.legend_kick = QWidget()
        lbl_dot_kck = QLabel("● ")
        lbl_dot_kck.setProperty("role", "caption")
        lbl_dot_kck.setStyleSheet(f"color: {COLOR_GREEN};")
        lbl_txt_kck = QLabel(self.i18n.get("network.services.kick"))
        lbl_txt_kck.setProperty("role", "caption")
        lay_kck = QHBoxLayout(self.legend_kick)
        lay_kck.setContentsMargins(0, 0, 0, 0)
        lay_kck.setSpacing(2)
        lay_kck.addWidget(lbl_dot_kck)
        lay_kck.addWidget(lbl_txt_kck)
        
        self.legend_layout.addWidget(self.legend_internet)
        self.legend_layout.addWidget(self.legend_kick)
        
        self.main_layout.addLayout(self.legend_layout)
        
        self._update_labels()
        
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

class NetworkStatusCard(QFrame):
    def __init__(self, key: str, title: str, description: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.key = key
        self.setProperty("role", "card")
        self.setMinimumWidth(285)
        self.setFixedHeight(80)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 10, 12, 10)
        self.layout.setSpacing(10)
        
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedSize(32, 32)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.lbl_icon)
        
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setProperty("role", "h3")
        self.info_layout.addWidget(self.lbl_title)
        
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setProperty("role", "body")
        self.lbl_desc.setWordWrap(True)
        self.info_layout.addWidget(self.lbl_desc)
        
        self.layout.addLayout(self.info_layout, stretch=1)
        
        self.status_layout = QVBoxLayout()
        self.status_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_layout.setSpacing(2)
        
        self.lbl_status = QLabel()
        self.lbl_status.setProperty("role", "body")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_layout.addWidget(self.lbl_status)
        
        self.lbl_latency = QLabel()
        self.lbl_latency.setProperty("role", "caption")
        self.lbl_latency.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_layout.addWidget(self.lbl_latency)
        
        self.layout.addLayout(self.status_layout)
        
        self.icon_name = icon_name
        self.set_icon(COLOR_NEUTRAL_200)
        
    def set_icon(self, color_hex: str):
        icon = get_icon_colored(self.icon_name, color_hex, size=20)
        self.lbl_icon.setPixmap(icon.pixmap(20, 20))
        
    def set_status(self, status: str, latency: int, status_text: str):
        if status == "checking":
            color = COLOR_NEUTRAL_500
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText("")
            self.set_icon(COLOR_NEUTRAL_500)
        elif status == "online":
            color = COLOR_GREEN
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText(f"{latency} ms")
            self.set_icon(COLOR_GREEN)
        elif status == "warning":
            color = COLOR_AMBER
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText(f"{latency} ms")
            self.set_icon(COLOR_AMBER)
        else:
            color = COLOR_RED
            self.lbl_status.setText(status_text)
            self.lbl_latency.setText("-")
            self.set_icon(COLOR_RED)
            
        self.lbl_status.setStyleSheet(f"color: {color}; font-weight: bold;")

    def sizeHint(self):
        return QSize(285, 80)

class NetworkView(BaseView):
    check_requested = Signal()
    view_shown = Signal()

    def __init__(self, i18n):
        super().__init__(
            i18n=i18n,
            title_key="network.header.title",
            subtitle_key="network.header.subtitle"
        )
        self.cards = {}
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        self.btn_check = ModernButton(self.i18n.get("network.btn_check"), role="action_accent")
        self.btn_check.setIcon(get_icon_colored("refresh.svg", COLOR_BLACK, 16))
        self.btn_check.setFixedWidth(200)
        self.btn_check.clicked.connect(self.check_requested.emit)
        btn_layout.addWidget(self.btn_check)
        btn_layout.addStretch()
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addSpacing(10)
        
        self.graph = LiveNetworkGraph(self.i18n, self)
        self.main_layout.addWidget(self.graph)
        self.main_layout.addSpacing(10)
        
        cards_container = QWidget()
        self.cards_layout = FlowLayout(cards_container, margin=0, hspacing=12, vspacing=12)
        
        self._add_card("internet", self.i18n.get("network.services.internet"), self.i18n.get("network.services.internet_desc"), "wifi.svg")
        self._add_card("chat_websocket", self.i18n.get("network.services.chat_websocket"), self.i18n.get("network.services.chat_websocket_desc"), "message.svg")
        self._add_card("overlay", self.i18n.get("network.services.overlay"), self.i18n.get("network.services.overlay_desc"), "plug.svg")
        self._add_card("kick", self.i18n.get("network.services.kick"), self.i18n.get("network.services.kick_desc"), "kick.svg")
        self._add_card("spotify", self.i18n.get("network.services.spotify"), self.i18n.get("network.services.spotify_desc"), "spotify.svg")
        self._add_card("youtube", self.i18n.get("network.services.youtube"), self.i18n.get("network.services.youtube_desc"), "brand-youtube.svg")
        
        self.main_layout.addWidget(cards_container)
        self.main_layout.addStretch()

    def _add_card(self, key: str, title: str, description: str, icon: str):
        card = NetworkStatusCard(key, title, description, icon, self)
        self.cards[key] = card
        self.cards_layout.addWidget(card)

    def set_checking_state(self):
        self.btn_check.setEnabled(False)
        for card in self.cards.values():
            card.set_status("checking", -1, self.i18n.get("network.status.checking"))

    def update_status(self, results: dict):
        self.btn_check.setEnabled(True)
        for key, info in results.items():
            if key in self.cards:
                status = info["status"]
                latency = info["latency"]
                
                status_text = self.i18n.get(f"network.status.{status}")
                self.cards[key].set_status(status, latency, status_text)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()
