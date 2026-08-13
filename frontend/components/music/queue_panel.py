# frontend\components\music\queue_panel.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView, QAbstractItemView, QTableWidgetItem
from PySide6.QtCore import Signal, Qt, QSize, QRect, QRectF
from PySide6.QtGui import QPainter, QPen, QColor
from frontend.common.theme import COLOR_RED, COLOR_NEUTRAL_400, COLOR_GREEN
from frontend.common.utils import get_icon_colored
from frontend.widgets import ModernTable, ModernTableCard

class DragDropQueueTable(ModernTable):
    row_moved = Signal(int, int)

    def __init__(self, headers: list[str], parent=None):
        super().__init__(headers, parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.TargetMoveAction)
        self._drag_start_row = -1
        self.pending_select_row = -1
        self._drop_target_row = -1

    def dragEnterEvent(self, event):
        if event.source() == self:
            self._drag_start_row = self.currentRow()
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.acceptProposedAction()
            pos = event.position().toPoint() if hasattr(event.position(), "toPoint") else event.pos()
            drop_item = self.itemAt(pos)
            if drop_item:
                target_row = drop_item.row()
            else:
                target_row = max(0, self.rowCount() - 1) if self.rowCount() > 0 else 0

            if self._drop_target_row != target_row:
                self._drop_target_row = target_row
                self.viewport().update()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self._drop_target_row = -1
        self.viewport().update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._drop_target_row = -1
        self.viewport().update()
        if event.source() == self:
            pos = event.position().toPoint() if hasattr(event.position(), "toPoint") else event.pos()
            drop_item = self.itemAt(pos)
            target_row = drop_item.row() if drop_item else (self.rowCount() - 1)
            source_row = self._drag_start_row if self._drag_start_row != -1 else self.currentRow()

            event.acceptProposedAction()
            event.accept()

            if source_row != -1 and target_row != -1 and source_row != target_row:
                self.pending_select_row = target_row
                self.row_moved.emit(source_row, target_row)

            self._drag_start_row = -1
        else:
            super().dropEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self._drop_target_row != -1 and self.rowCount() > 0:
            row = min(max(0, self._drop_target_row), self.rowCount() - 1)
            row_rect = QRect()
            for col in range(self.columnCount()):
                rect = self.visualRect(self.model().index(row, col))
                if row_rect.isEmpty():
                    row_rect = rect
                else:
                    row_rect = row_rect.united(rect)
                    
            if not row_rect.isEmpty():
                painter = QPainter(self.viewport())
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.fillRect(row_rect, QColor(46, 205, 112, 22))
                pen = QPen(QColor(COLOR_GREEN), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                target_draw_rect = QRectF(row_rect).adjusted(1, 1, -1, -1)
                painter.drawRoundedRect(target_draw_rect, 6, 6)
                painter.end()

class MusicQueuePanel(QWidget):
    remove_queue_item_requested = Signal(int)
    move_queue_item_requested = Signal(int, int)
    queue_updated = Signal(int, str)

    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self._current_queue_urls = []
        
        self._icon_delete = get_icon_colored("trash.svg", COLOR_RED, 14)
        self._icon_grip = get_icon_colored("grip-vertical.svg", COLOR_NEUTRAL_400, 14)
        
        self._setup_ui()

    def _setup_ui(self):
        panel_layout = QVBoxLayout(self)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        headers = [
            self.i18n.get("music.queue.col_num"),
            self.i18n.get("music.queue.col_title"),
            self.i18n.get("music.queue.col_artist"),
            self.i18n.get("music.queue.col_requester"),
            self.i18n.get("music.queue.col_duration"),
            self.i18n.get("music.queue.col_actions")
        ]

        self.card_queue = ModernTableCard(
            title_text=self.i18n.get("music.queue.title"),
            headers=headers
        )
        self.card_queue.setVisible(False)
        
        old_table = self.card_queue.table
        self.card_queue.stack.removeWidget(old_table)
        old_table.deleteLater()

        self.queue_table = DragDropQueueTable(headers, parent=self.card_queue)
        self.card_queue.table = self.queue_table
        self.card_queue.stack.insertWidget(0, self.queue_table)
        self.card_queue.stack.setCurrentIndex(0)

        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.queue_table.setShowGrid(False)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.horizontalHeader().setHighlightSections(False)
        
        self.queue_table.row_moved.connect(self.move_queue_item_requested.emit)

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
            icon_name="illustration-music.svg",
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

    def _create_action_buttons(self, index: int) -> QWidget:
        cell_widget = QWidget()
        cell_layout = QHBoxLayout(cell_widget)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(4)
        cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_delete = QPushButton()
        btn_delete.setProperty("role", "btn_ghost")
        btn_delete.setIcon(self._icon_delete)
        btn_delete.setIconSize(QSize(14, 14))
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setToolTip(self.i18n.get("music.queue.remove_tooltip"))
        btn_delete.setFixedSize(QSize(24, 24))
        btn_delete.clicked.connect(lambda *args, idx=index: self.remove_queue_item_requested.emit(idx))

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
        new_signature = [(song.get("url") or song.get("title"), song.get("artist"), song.get("duration")) for song in queue_items]
        if getattr(self, "_current_queue_signature", None) == new_signature:
            return
        self._current_queue_signature = new_signature

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
            
        self.queue_table.setUpdatesEnabled(False)
        try:
            self.queue_table.setRowCount(len(queue_items))
            for idx, song in enumerate(queue_items):
                item_num = self._create_table_item(f"  {idx + 1}", Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, Qt.GlobalColor.gray)
                item_num.setIcon(self._icon_grip)
                self.queue_table.setItem(idx, 0, item_num)
                
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
                self.queue_table.setCellWidget(idx, 5, self._create_action_buttons(idx))
        finally:
            self.queue_table.setUpdatesEnabled(True)

        if hasattr(self.queue_table, "pending_select_row") and self.queue_table.pending_select_row != -1:
            target_r = self.queue_table.pending_select_row
            self.queue_table.pending_select_row = -1
            if 0 <= target_r < total_songs:
                self.queue_table.selectRow(target_r)
