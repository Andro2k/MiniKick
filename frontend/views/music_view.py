# frontend\views\music_view.py

from frontend.common.theme import COLOR_DANGER
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                                QLabel, QFrame, QScrollArea, QComboBox, QSlider, QPushButton,
                                QLayout)
from PySide6.QtCore import Qt, Signal, QSize, QPoint, QRect

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, hspacing=8, vspacing=8):
        super().__init__(parent)
        self._item_list = []
        self._hspacing = hspacing
        self._vspacing = vspacing
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        h_space = self._hspacing
        v_space = self._vspacing

        for item in self._item_list:
            wid = item.widget()
            next_x = x + item.sizeHint().width() + h_space
            if next_x - h_space > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + v_space
                next_x = x + item.sizeHint().width() + h_space
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - effective_rect.y() + top + bottom

from frontend.common.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY
from frontend.common.utils import get_icon_colored, get_icon
from frontend.widgets.blocks_component import ViewHeader, SettingRow, SliderRow
from frontend.widgets.controls_component import ModernButton, ModernSwitch

class MusicView(QWidget):
    connect_requested = Signal()
    disconnect_requested = Signal()
    command_toggled = Signal(str, bool)
    provider_changed = Signal(str)
    volume_changed = Signal(int)
    remove_queue_item_requested = Signal(int)

    def __init__(self, i18n):
        super().__init__()
        self.i18n = i18n
        self._setup_ui()

    def _setup_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(16)

        self.header = ViewHeader(
            title_text=self.i18n.get("music.header.title"),
            subtitle_text=self.i18n.get("music.header.subtitle"),
            icon_name="headphones.svg",
            icon_color=COLOR_TEXT_PRIMARY
        )
        self.main_layout.addWidget(self.header)

        self._setup_provider_selection_card()
        self._setup_auth_card()
        self._setup_now_playing_card()
        self._setup_queue_card()
        self._setup_commands_card()

        self.main_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        base_layout.addWidget(scroll_area)

    def _setup_provider_selection_card(self):
        card = QFrame()
        card.setProperty("role", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        self.combo_provider = QComboBox()
        self.combo_provider.addItem("Spotify", "spotify")
        self.combo_provider.addItem("YouTube", "youtube")
        
        self.combo_provider.currentIndexChanged.connect(
            lambda: self.provider_changed.emit(self.combo_provider.currentData())
        )

        row_provider = SettingRow(
            icon_name="headphones.svg",
            title_text=self.i18n.get("music.provider.select_title"),
            desc_text=self.i18n.get("music.provider.select_desc"),
            right_widget=self.combo_provider
        )
        layout.addWidget(row_provider)
        self.main_layout.addWidget(card)

    def _setup_auth_card(self):
        card = QFrame()
        card.setProperty("role", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        status_layout = QHBoxLayout()
        self.lbl_provider_name = QLabel(self.i18n.get("music.provider.name"))
        self.lbl_provider_name.setProperty("role", "h2")
        
        self.lbl_auth_status = QLabel(self.i18n.get("common.status.disconnected"))
        self.lbl_auth_status.setProperty("role", "body")
        
        provider_info = QVBoxLayout()
        provider_info.addWidget(self.lbl_provider_name)
        provider_info.addWidget(self.lbl_auth_status)

        self.btn_connect = ModernButton(self.i18n.get("common.buttons.connect"), role="action_accent")
        self.btn_connect.clicked.connect(self.connect_requested.emit)

        self.btn_disconnect = ModernButton(self.i18n.get("common.buttons.disconnect"), role="action_danger_border")
        self.btn_disconnect.setVisible(False)
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)

        status_layout.addLayout(provider_info, stretch=1)
        status_layout.addWidget(self.btn_connect)
        status_layout.addWidget(self.btn_disconnect)

        layout.addLayout(status_layout)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "body")
        
        self.row_vol = SliderRow(
            icon_name="volume.svg",
            title_text=self.i18n.get("music.player.volume_title"),
            desc_text=self.i18n.get("music.player.volume_desc"),
            slider_widget=self.slider_vol,
            value_label=self.lbl_vol_perc
        )
        self.row_vol.setVisible(False)
        self.slider_vol.valueChanged.connect(self._on_volume_slider_changed)
        layout.addWidget(self.row_vol)

        self.main_layout.addWidget(card)

    def _on_volume_slider_changed(self, val):
        self.lbl_vol_perc.setText(f"{val}%")
        self.volume_changed.emit(val)

    def _setup_now_playing_card(self):
        self.card_player = QFrame()
        self.card_player.setProperty("role", "card")
        self.card_player.setVisible(False)
        
        layout = QHBoxLayout(self.card_player)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.icon_music = QLabel()
        self.icon_music.setPixmap(get_icon_colored("spotify.svg", COLOR_ACCENT, 32).pixmap(32, 32))
        
        info_layout = QVBoxLayout()
        self.lbl_song_title = QLabel(self.i18n.get("music.player.not_playing"))
        self.lbl_song_title.setProperty("role", "h2")
        self.lbl_song_title.setWordWrap(True)
        
        self.lbl_song_artist = QLabel("-")
        self.lbl_song_artist.setProperty("role", "body")
        self.lbl_song_artist.setWordWrap(True)

        info_layout.addWidget(self.lbl_song_title)
        info_layout.addWidget(self.lbl_song_artist)

        layout.addWidget(self.icon_music, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(info_layout, stretch=1)
        
        self.main_layout.addWidget(self.card_player)

    def _setup_commands_card(self):
        self.card_cmds = QFrame()
        self.card_cmds.setProperty("role", "card")
        self.card_cmds.setEnabled(False)
        
        layout = QVBoxLayout(self.card_cmds)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        lbl_title = QLabel(self.i18n.get("music.cmds.title"))
        lbl_title.setProperty("role", "h2")
        layout.addWidget(lbl_title)

        self.sw_sr = ModernSwitch()
        self.sw_sr.toggled.connect(lambda val: self.command_toggled.emit("!sr", val))
        row_sr = SettingRow("add.svg", self.i18n.get("music.cmds.sr_label"), self.i18n.get("music.cmds.sr_desc"), self.sw_sr)

        self.sw_skip = ModernSwitch()
        self.sw_skip.toggled.connect(lambda val: self.command_toggled.emit("!skip", val))
        row_skip = SettingRow("player-skip-forward.svg", self.i18n.get("music.cmds.skip_label"), self.i18n.get("music.cmds.skip_desc"), self.sw_skip)

        self.sw_song = ModernSwitch()
        self.sw_song.toggled.connect(lambda val: self.command_toggled.emit("!song", val))
        row_song = SettingRow("info-circle.svg", self.i18n.get("music.cmds.song_label"), self.i18n.get("music.cmds.song_desc"), self.sw_song)

        layout.addWidget(row_sr)
        layout.addWidget(row_skip)
        layout.addWidget(row_song)
        
        self.main_layout.addWidget(self.card_cmds)

    def _setup_queue_card(self):
        self.card_queue = QFrame()
        self.card_queue.setProperty("role", "card")
        self.card_queue.setVisible(False)
        
        layout = QVBoxLayout(self.card_queue)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        header_layout = QHBoxLayout()
        lbl_title = QLabel(self.i18n.get("music.queue.title"))
        lbl_title.setProperty("role", "h2")
        
        self.lbl_queue_count = QLabel("(0)")
        self.lbl_queue_count.setProperty("role", "caption")
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(self.lbl_queue_count)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.queue_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_scroll.setMinimumHeight(120)
        self.queue_scroll.setMaximumHeight(260)
        
        self.queue_list_widget = QWidget()
        self.queue_list_layout = FlowLayout(self.queue_list_widget, margin=0, hspacing=8, vspacing=8)
        
        self.queue_scroll.setWidget(self.queue_list_widget)
        layout.addWidget(self.queue_scroll)
        
        self.lbl_empty_queue = QLabel(self.i18n.get("music.queue.empty"))
        self.lbl_empty_queue.setProperty("role", "body")
        self.lbl_empty_queue.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.queue_list_layout.addWidget(self.lbl_empty_queue)
        
        self.main_layout.addWidget(self.card_queue)

    def update_queue(self, queue_items: list[dict]):
        while self.queue_list_layout.count() > 0:
            item = self.queue_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        self.lbl_queue_count.setText(f"({len(queue_items)})")
        
        if not queue_items:
            self.lbl_empty_queue = QLabel(self.i18n.get("music.queue.empty"))
            self.lbl_empty_queue.setProperty("role", "body")
            self.lbl_empty_queue.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.queue_list_layout.addWidget(self.lbl_empty_queue)
            return

        for idx, song in enumerate(queue_items):
            item_frame = QFrame()
            item_frame.setFixedSize(265, 48)
            item_frame.setProperty("role", "bot_tag")
            
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(10, 6, 10, 6)
            item_layout.setSpacing(10)
            
            lbl_idx = QLabel(f"{idx + 1}")
            lbl_idx.setProperty("role", "caption")
            lbl_idx.setFixedWidth(16)
            item_layout.addWidget(lbl_idx)
            
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            
            title_text = song.get("title", "Unknown Title")
            if len(title_text) > 28:
                title_text = title_text[:25] + "..."
                
            artist_text = song.get("artist", "-")
            requester = song.get("requester")
            lbl_artist_text = artist_text
            if requester:
                lbl_artist_text += f" • Pedida por @{requester}"
            if len(lbl_artist_text) > 36:
                lbl_artist_text = lbl_artist_text[:33] + "..."
            
            lbl_title = QLabel(title_text)
            lbl_title.setProperty("role", "h3")
            lbl_title.setWordWrap(False)
                
            lbl_artist = QLabel(lbl_artist_text)
            lbl_artist.setProperty("role", "caption")
            lbl_artist.setWordWrap(False)
            
            info_layout.addWidget(lbl_title)
            info_layout.addWidget(lbl_artist)
            item_layout.addLayout(info_layout, stretch=1)
            
            btn_delete = QPushButton()
            btn_delete.setProperty("role", "btn_ghost")
            btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_DANGER, 14))
            btn_delete.setIconSize(QSize(14, 14))
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setToolTip(self.i18n.get("music.queue.remove_tooltip"))
            btn_delete.setFixedSize(QSize(26, 26))
            
            btn_delete.clicked.connect(lambda *args, index=idx: self.remove_queue_item_requested.emit(index))
            item_layout.addWidget(btn_delete)
            
            self.queue_list_layout.addWidget(item_frame)

    def set_auth_state(self, connected: bool, label_key: str = ""):
        provider = self.combo_provider.currentData()
        
        if provider == "youtube":
            self.lbl_provider_name.setText("YouTube")
            self.icon_music.setPixmap(get_icon("youtube.svg").pixmap(32, 32))
            self.btn_connect.setVisible(False)
            self.btn_disconnect.setVisible(False)
            self.card_cmds.setEnabled(True)
            self.card_player.setVisible(True)
            self.card_queue.setVisible(True)
            self.row_vol.setVisible(True)
            translated_label = self.i18n.get("music.status.youtube_active")
            self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
        else:
            self.lbl_provider_name.setText(self.i18n.get("music.provider.name"))
            self.icon_music.setPixmap(get_icon_colored("spotify.svg", COLOR_ACCENT, 32).pixmap(32, 32))
            self.btn_connect.setVisible(not connected)
            self.btn_connect.setEnabled(not connected)
            self.btn_disconnect.setVisible(connected)
            self.card_cmds.setEnabled(connected)
            self.card_player.setVisible(connected)
            self.card_queue.setVisible(False)
            self.row_vol.setVisible(False)

            if connected:
                translated_label = self.i18n.get(label_key) or label_key
                self.lbl_auth_status.setText(f"{self.i18n.get('common.status.active')}: {translated_label}")
            else:
                self.lbl_auth_status.setText(self.i18n.get("common.status.disconnected"))

    def update_current_song(self, song_data: dict | None):
        if not song_data:
            self.lbl_song_title.setText(self.i18n.get("music.player.paused_title"))
            self.lbl_song_artist.setText(self.i18n.get("music.player.paused_desc"))
            return

        self.lbl_song_title.setText(song_data.get("title", ""))
        self.lbl_song_artist.setText(song_data.get("artist", ""))