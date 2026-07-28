# frontend\components\music\queue_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Signal, Qt, QSize
from frontend.common.theme import COLOR_RED, COLOR_NEUTRAL_200
from frontend.common.utils import get_icon_colored
from frontend.widgets import ModernTableCard

class MusicQueuePanel(QWidget):
    remove_queue_item_requested = Signal(int)
    move_queue_item_requested = Signal(int, int)
    queue_updated = Signal(int, str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._current_queue_urls = []
        self._setup_ui()

    def _setup_ui(self):
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        self.card_queue = ModernTableCard(
            title_text=self.i18n.get("music.queue.title"),
            headers=[
                self.i18n.get("music.queue.col_num"),
                self.i18n.get("music.queue.col_title"),
                self.i18n.get("music.queue.col_artist"),
                self.i18n.get("music.queue.col_requester"),
                self.i18n.get("music.queue.col_duration"),
                self.i18n.get("music.queue.col_actions")
            ]
        )
        self.card_queue.setVisible(False)
        
        self.queue_table = self.card_queue.table
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.queue_table.setShowGrid(False)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.horizontalHeader().setHighlightSections(False)
        
        column_stretch_modes = {
            0: QHeaderView.ResizeMode.ResizeToContents,
            1: QHeaderView.ResizeMode.Stretch,
            2: QHeaderView.ResizeMode.Stretch,
            3: QHeaderView.ResizeMode.ResizeToContents,
            4: QHeaderView.ResizeMode.ResizeToContents,
            5: QHeaderView.ResizeMode.ResizeToContents
        }
        for col, mode in column_stretch_modes.items():
            self.queue_table.horizontalHeader().setSectionResizeMode(col, mode)
        
        self.queue_table.setMinimumHeight(200)
        
        self.card_queue.setup_empty_state(
            title=self.i18n.get("music.queue.empty"),
            desc=self.i18n.get("music.queue.empty_desc"),
            icon_name="illustration_music.svg",
            button_text="",
            on_button_clicked=lambda: None
        )
        if hasattr(self.card_queue, "btn_empty_action") and self.card_queue.btn_empty_action:
            self.card_queue.btn_empty_action.setVisible(False)
            
        panel_layout.addWidget(self.card_queue)

    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = None, color: Qt.GlobalColor = None) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if alignment is not None:
            item.setTextAlignment(alignment)
        if color is not None:
            item.setForeground(color)
        return item

    def _create_action_buttons(self, index: int, total_count: int) -> QWidget:
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(4)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_up = QPushButton()
        btn_up.setProperty("role", "btn_ghost")
        btn_up.setIcon(get_icon_colored("chevron-up.svg", COLOR_NEUTRAL_200, 14))
        btn_up.setIconSize(QSize(14, 14))
        btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_up.setFixedSize(QSize(24, 24))
        btn_up.setEnabled(index > 0)
        btn_up.clicked.connect(lambda *args, idx=index: self.move_queue_item_requested.emit(idx, idx - 1))

        btn_down = QPushButton()
        btn_down.setProperty("role", "btn_ghost")
        btn_down.setIcon(get_icon_colored("chevron-down.svg", COLOR_NEUTRAL_200, 14))
        btn_down.setIconSize(QSize(14, 14))
        btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_down.setFixedSize(QSize(24, 24))
        btn_down.setEnabled(index < total_count - 1)
        btn_down.clicked.connect(lambda *args, idx=index: self.move_queue_item_requested.emit(idx, idx + 1))

        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setIcon(get_icon_colored("trash.svg", COLOR_RED, 14))
        btn_delete.setIconSize(QSize(14, 14))
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setToolTip(self.i18n.get("music.queue.remove_tooltip"))
        btn_delete.setFixedSize(QSize(24, 24))
        btn_delete.clicked.connect(lambda *args, idx=index: self.remove_queue_item_requested.emit(idx))

        cell_layout.addWidget(btn_up)
        cell_layout.addWidget(btn_down)
        cell_layout.addWidget(btn_delete)
        return cell_widget

    def _parse_duration_to_seconds(self, dur_str: str) -> int:
        if not dur_str or dur_str == "-":
            return 0
        parts = str(dur_str).strip().split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 1 and parts[0].isdigit():
                return int(parts[0])
        except ValueError:
            pass
        return 0

    def _format_seconds_to_hms(self, total_seconds: int) -> str:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def update_queue(self, queue_items: list[dict]):
        new_urls = [song.get("url") for song in queue_items]
        if self._current_queue_urls == new_urls:
            return
        self._current_queue_urls = new_urls

        total_songs = len(queue_items)
        total_secs = sum(self._parse_duration_to_seconds(song.get("duration", "")) for song in queue_items)
        duration_str = self._format_seconds_to_hms(total_secs)

        self.queue_updated.emit(total_songs, duration_str)

        if hasattr(self.card_queue, "lbl_title") and self.card_queue.lbl_title:
            title_base = self.i18n.get("music.queue.title")
            self.card_queue.lbl_title.setText(f"{title_base} ({total_songs})")
        
        self.card_queue.set_empty(total_songs == 0)
        
        if not queue_items:
            self.queue_table.setRowCount(0)
            return
            
        self.queue_table.setRowCount(len(queue_items))
        
        for idx, song in enumerate(queue_items):
            self.queue_table.setItem(idx, 0, self._create_table_item(f"{idx + 1}", Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.gray))
            
            title_text = song.get("title", self.i18n.get("music.player.unknown_song"))
            self.queue_table.setItem(idx, 1, self._create_table_item(title_text))
            
            artist_text = song.get("artist", "-")
            self.queue_table.setItem(idx, 2, self._create_table_item(artist_text))
            
            requester = song.get("requester", "")
            requester_text = f"@{requester}" if requester else "-"
            req_color = Qt.GlobalColor.green if requester else None
            self.queue_table.setItem(idx, 3, self._create_table_item(requester_text, color=req_color))
            
            duration = song.get("duration", "-")
            self.queue_table.setItem(idx, 4, self._create_table_item(duration, Qt.AlignmentFlag.AlignCenter))
            self.queue_table.setCellWidget(idx, 5, self._create_action_buttons(idx, total_songs))
