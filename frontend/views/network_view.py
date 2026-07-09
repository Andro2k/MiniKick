# frontend\views\network_view.py

import random
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFrame, QLabel, QWidget
from PySide6.QtCore import Qt, Signal, QTimer, QPointF, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QPainterPath, QFont
from frontend.common.utils import get_icon_colored
from frontend.widgets.base_view import BaseView
from frontend.widgets.controls_component import ModernButton
from frontend.widgets.flow_layout import FlowLayout
from frontend.common.theme import (
    COLOR_NEUTRAL_200, COLOR_NEUTRAL_500, 
    COLOR_GREEN, COLOR_AMBER, COLOR_RED, COLOR_BLACK
)

class GraphCanvas(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_graph = parent
        
    def paintEvent(self, event):
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
            
        history = self.parent_graph.latency_history
        max_val = max(80.0, max(history))
        max_scale = ((int(max_val) // 40) + 1) * 40  
        grid_lines = 4
        painter.setFont(QFont("Inter", 8))
        
        for i in range(grid_lines + 1):
            val = (max_scale / grid_lines) * i
            y = self.height() - bottom_margin - (val / max_scale) * H
            
            if i > 0 and i < grid_lines:
                painter.setPen(QPen(QColor(255, 255, 255, 12), 1, Qt.PenStyle.DashLine))
                painter.drawLine(left_margin, y, self.width() - right_margin, y)
                
            painter.setPen(QColor("#6B7280"))
            painter.drawText(5, y + 4, f"{int(val)} ms")

        painter.setPen(QColor("#6B7280"))
        painter.drawText(left_margin, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_45s"))
        painter.drawText(left_margin + W // 2 - 15, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_20s"))
        painter.drawText(self.width() - right_margin - 30, self.height() - 5, self.parent_graph.i18n.get("network.graph.time_now"))

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
            
            gradient = QLinearGradient(0, top_margin, 0, self.height() - bottom_margin)
            gradient.setColorAt(0.0, QColor(83, 252, 24, 45))
            gradient.setColorAt(1.0, QColor(83, 252, 24, 0))
            painter.fillPath(fill_path, QBrush(gradient))
            
            pen = QPen(QColor(COLOR_GREEN), 2.0)
            painter.setPen(pen)
            painter.drawPath(path)

class LiveNetworkGraph(QFrame):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.setProperty("role", "card")
        self.setFixedHeight(280)
        
        self.latency_history = [35.0] * 50
        self.current_latency = 35
        self.avg_latency = 35
        self.max_latency = 35
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)
        self.main_layout.setSpacing(10)
        
        self.header_layout = QHBoxLayout()
        self.header_layout.setSpacing(12)
        
        self.lbl_title = QLabel(self.i18n.get("network.graph.title"))
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        
        self.stats_container = QWidget()
        self.stats_layout = QHBoxLayout(self.stats_container)
        self.stats_layout.setContentsMargins(0, 0, 0, 0)
        self.stats_layout.setSpacing(15)
        
        self.lbl_live = QLabel()
        self.lbl_live.setStyleSheet("font-size: 12px; color: #53fc18; font-weight: 500;")
        
        self.lbl_avg = QLabel()
        self.lbl_avg.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 500;")
        
        self.lbl_max = QLabel()
        self.lbl_max.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 500;")
        
        self.stats_layout.addWidget(self.lbl_live)
        self.stats_layout.addWidget(self.lbl_avg)
        self.stats_layout.addWidget(self.lbl_max)
        
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.stats_container)
        
        self.main_layout.addLayout(self.header_layout)
        
        self.canvas = GraphCanvas(self)
        self.main_layout.addWidget(self.canvas, stretch=1)
        
        self._update_labels()
        
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._update_simulation)
        self.sim_timer.start(1000)
        
    def _update_labels(self):
        live_lbl = self.i18n.get("network.graph.live")
        avg_lbl = self.i18n.get("network.graph.avg")
        max_lbl = self.i18n.get("network.graph.max")
        
        self.lbl_live.setText(f"{live_lbl}: {int(self.latency_history[-1])} ms")
        self.lbl_avg.setText(f"{avg_lbl}: {self.avg_latency} ms")
        self.lbl_max.setText(f"{max_lbl}: {self.max_latency} ms")
        
    def _update_simulation(self):
        import random
        last_val = self.latency_history[-1]
        noise = random.uniform(-4.0, 4.0)
        drift_correction = (self.current_latency - last_val) * 0.1
        new_val = max(5.0, min(999.0, last_val + noise + drift_correction))
        
        self.latency_history.pop(0)
        self.latency_history.append(new_val)
        
        active_points = [p for p in self.latency_history if p > 0]
        if active_points:
            self.avg_latency = int(sum(active_points) / len(active_points))
            self.max_latency = int(max(active_points))
            
        self._update_labels()
        self.canvas.update()
        
    def add_real_measurement(self, latency: int):
        self.current_latency = latency
        self.latency_history.pop(0)
        self.latency_history.append(float(latency))
        
        active_points = [p for p in self.latency_history if p > 0]
        if active_points:
            self.avg_latency = int(sum(active_points) / len(active_points))
            self.max_latency = int(max(active_points))
            
        self._update_labels()
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
        latencies = []
        for key, info in results.items():
            if key in self.cards:
                status = info["status"]
                latency = info["latency"]
                
                status_text = self.i18n.get(f"network.status.{status}")
                self.cards[key].set_status(status, latency, status_text)
                
                if key != "overlay" and status == "online" and latency > 0:
                    latencies.append(latency)
                    
        if latencies:
            avg_lat = int(sum(latencies) / len(latencies))
            self.graph.add_real_measurement(avg_lat)

    def showEvent(self, event):
        super().showEvent(event)
        self.view_shown.emit()
