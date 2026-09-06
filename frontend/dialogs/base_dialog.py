# frontend\dialogs\base_dialog.py

import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                               QStackedWidget, QProgressBar, QWidget, QScrollArea, QApplication)
from PySide6.QtCore import Qt, QSize, QSettings, QEvent
from PySide6.QtGui import QIcon, QColor, QMouseEvent, QKeyEvent
from frontend.common import (
    COLOR_RED, COLOR_AMBER, COLOR_BLUE, COLOR_GREEN,
    COLOR_TWITCH, COLOR_YOUTUBE, COLOR_TIKTOK, COLOR_BLACK,
    COLOR_WHITE, PATH_ICON_HELP
)

logger = logging.getLogger("minikick.dialogs.base_dialog")

class ModernFramelessShell(QDialog):
    _icon_close = None
    RESIZE_MARGIN = 8

    def __init__(
        self,
        width: int = 420,
        height: int | None = None,
        resizable: bool = False,
        min_width: int = 380,
        min_height: int = 320,
        dialog_key: str | None = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self._old_drag_pos = None
        self._resizable = resizable
        self._base_width = width
        self._base_height = height
        self._min_width = min_width
        self._min_height = min_height
        self._dialog_key = dialog_key
        self._has_custom_size = False
        self._active_resize_edge = None
        self._resize_start_mouse_pos = None
        self._resize_start_window_geo = None
        self._resize_start_container_size = None

        if self._resizable:
            self.setMouseTracking(True)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame(self)
        self.container.setProperty("role", "dialog")
        if self._resizable:
            self.container.setMouseTracking(True)
            self.container.installEventFilter(self)

        init_w = width
        init_h = height
        if dialog_key:
            try:
                settings = QSettings("MiniKick", "MiniKick")
                saved_w = settings.value(f"dialog_size/{dialog_key}/width", None, type=int)
                saved_h = settings.value(f"dialog_size/{dialog_key}/height", None, type=int)
                if saved_w and saved_w >= min_width:
                    init_w = saved_w
                    self._has_custom_size = True
                if saved_h and saved_h >= min_height:
                    init_h = saved_h
                    self._has_custom_size = True
            except Exception as e:
                logger.debug("Failed to load saved dialog size for %s: %s", dialog_key, e)

        if height is not None:
            self._has_custom_size = True

        if self._resizable:
            self.container.setMinimumSize(min_width, min_height)
            if init_h is not None:
                self.container.setFixedSize(init_w, init_h)
            else:
                self.container.setFixedWidth(init_w)
                self.container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        else:
            self.container.setFixedWidth(init_w)
            if init_h is not None:
                self.container.setFixedHeight(init_h)
            self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setOffset(0, 0)
        self.glow.setColor(QColor(0, 0, 0, 0))
        self.container.setGraphicsEffect(self.glow)

        self.main_layout.addWidget(self.container)

        from frontend.common import get_icon_colored

        self.btn_close_shell = QPushButton(self.container)
        self.btn_close_shell.setProperty("role", "btn_ghost")
        self.btn_close_shell.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_shell.setFixedSize(28, 28)
        self.btn_close_shell.setAutoDefault(False)
        self.btn_close_shell.setDefault(False)
        if ModernFramelessShell._icon_close is None:
            ModernFramelessShell._icon_close = get_icon_colored("x.svg", size=14)
        self.btn_close_shell.setIcon(ModernFramelessShell._icon_close)
        self.btn_close_shell.setIconSize(QSize(14, 14))
        self.btn_close_shell.clicked.connect(self.reject)
        self.btn_close_shell.move(init_w - 36, 8)
        self.btn_close_shell.raise_()

    def set_dialog_dimensions(self, width: int, height: int):
        self._has_custom_size = True
        self.container.setFixedSize(width, height)
        self.resize(width + 32, height + 32)
        if hasattr(self, 'btn_close_shell'):
            self.btn_close_shell.move(width - 36, 8)
            self.btn_close_shell.raise_()

    def _apply_screen_constraints(self):
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            max_h = max(400, int(avail.height() * 0.92))
            max_w = max(400, int(avail.width() * 0.95))
            if not self._resizable:
                self.container.setMaximumHeight(max_h)
                self.setMaximumHeight(max_h + 32)
            else:
                self.container.setMaximumSize(max_w, max_h)
                self.setMaximumSize(max_w + 32, max_h + 32)

    def showEvent(self, event):
        self._apply_screen_constraints()
        if not self._resizable or not self._has_custom_size:
            self.adjustSize()
        else:
            self.resize(self.container.width() + 32, self.container.height() + 32)
        super().showEvent(event)
        parent_widget = self.parentWidget()
        if parent_widget and hasattr(parent_widget, "rect"):
            parent_rect = parent_widget.rect()
            parent_global_pos = parent_widget.mapToGlobal(parent_rect.topLeft())
            center_x = parent_global_pos.x() + (parent_rect.width() - self.width()) // 2
            center_y = parent_global_pos.y() + (parent_rect.height() - self.height()) // 2
        else:
            screen = self.screen() or QApplication.primaryScreen()
            if screen:
                avail = screen.availableGeometry()
                center_x = avail.left() + (avail.width() - self.width()) // 2
                center_y = avail.top() + (avail.height() - self.height()) // 2
            else:
                center_x, center_y = self.x(), self.y()

        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            center_x = max(avail.left(), min(center_x, avail.right() - self.width()))
            center_y = max(avail.top(), min(center_y, avail.bottom() - self.height()))

        self.move(center_x, center_y)
        if hasattr(self, 'btn_close_shell'):
            self.btn_close_shell.move(self.container.width() - 36, 8)
            self.btn_close_shell.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'btn_close_shell'):
            self.btn_close_shell.move(self.container.width() - 36, 8)
            self.btn_close_shell.raise_()

    def set_dialog_state(self, state: str, glow_color: QColor = None):
        self.container.setProperty("state", state)
        self.container.style().unpolish(self.container)
        self.container.style().polish(self.container)
        self.glow.setColor(glow_color if glow_color else QColor(0, 0, 0, 0))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.ignore()
            return
        super().keyPressEvent(event)

    def _detect_resize_edge(self, pos_in_container) -> tuple[str | None, Qt.CursorShape | None]:
        if not self._resizable:
            return None, None

        w = self.container.width()
        h = self.container.height()
        x = pos_in_container.x()
        y = pos_in_container.y()

        m = self.RESIZE_MARGIN
        outer_pad = 16

        if not (-outer_pad <= x <= w + outer_pad and -outer_pad <= y <= h + outer_pad):
            return None, None

        on_left = (-outer_pad <= x <= m)
        on_right = (w - m <= x <= w + outer_pad)
        on_top = (-outer_pad <= y <= m)
        on_bottom = (h - m <= y <= h + outer_pad)

        if on_top and on_left:
            return "top_left", Qt.CursorShape.SizeFDiagCursor
        if on_top and on_right:
            return "top_right", Qt.CursorShape.SizeBDiagCursor
        if on_bottom and on_left:
            return "bottom_left", Qt.CursorShape.SizeBDiagCursor
        if on_bottom and on_right:
            return "bottom_right", Qt.CursorShape.SizeFDiagCursor
        if on_left:
            return "left", Qt.CursorShape.SizeHorCursor
        if on_right:
            return "right", Qt.CursorShape.SizeHorCursor
        if on_top:
            return "top", Qt.CursorShape.SizeVerCursor
        if on_bottom:
            return "bottom", Qt.CursorShape.SizeVerCursor

        return None, None

    def eventFilter(self, watched, event):
        if self._resizable and watched == self.container:
            etype = event.type()
            if etype == QEvent.Type.MouseMove:
                if not self._active_resize_edge:
                    edge, cursor = self._detect_resize_edge(event.position().toPoint())
                    if cursor:
                        self.container.setCursor(cursor)
                    else:
                        self.container.unsetCursor()
            elif etype == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    edge, cursor = self._detect_resize_edge(event.position().toPoint())
                    if edge:
                        self._active_resize_edge = edge
                        self._resize_start_mouse_pos = event.globalPosition().toPoint()
                        self._resize_start_window_geo = self.geometry()
                        self._resize_start_container_size = self.container.size()
                        return True
            elif etype == QEvent.Type.MouseButtonRelease:
                if self._active_resize_edge:
                    self._finish_resizing()
                    return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event: QMouseEvent):
        if hasattr(self, 'btn_close_shell') and self.btn_close_shell.isVisible():
            local_pos = self.container.mapFrom(self, event.position().toPoint())
            if self.btn_close_shell.geometry().contains(local_pos):
                return super().mousePressEvent(event)

        if event.button() == Qt.MouseButton.LeftButton:
            pos_in_container = self.container.mapFrom(self, event.position().toPoint())
            edge, _ = self._detect_resize_edge(pos_in_container)
            if edge and self._resizable:
                self._active_resize_edge = edge
                self._resize_start_mouse_pos = event.globalPosition().toPoint()
                self._resize_start_window_geo = self.geometry()
                self._resize_start_container_size = self.container.size()
                event.accept()
                return

            self._old_drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._active_resize_edge:
            self._handle_resize_drag(event.globalPosition().toPoint())
            event.accept()
            return

        if self._old_drag_pos:
            delta = event.globalPosition().toPoint() - self._old_drag_pos
            self.move(self.pos() + delta)
            self._old_drag_pos = event.globalPosition().toPoint()
            event.accept()
            return

        if self._resizable:
            pos_in_container = self.container.mapFrom(self, event.position().toPoint())
            edge, cursor = self._detect_resize_edge(pos_in_container)
            if cursor:
                self.setCursor(cursor)
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._active_resize_edge:
            self._finish_resizing()
            event.accept()
            return
        self._old_drag_pos = None
        self.unsetCursor()
        if hasattr(self, 'container'):
            self.container.unsetCursor()
        event.accept()

    def _handle_resize_drag(self, cur_mouse_pos):
        if not self._active_resize_edge or not self._resize_start_mouse_pos:
            return

        delta = cur_mouse_pos - self._resize_start_mouse_pos
        start_w = self._resize_start_container_size.width()
        start_h = self._resize_start_container_size.height()
        start_x = self._resize_start_window_geo.x()
        start_y = self._resize_start_window_geo.y()

        screen = self.screen() or QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        max_w = int(avail.width() * 0.95) if avail else 1920
        max_h = int(avail.height() * 0.92) if avail else 1080

        min_w = self._min_width
        min_h = self._min_height

        edge = self._active_resize_edge

        new_w = start_w
        new_h = start_h
        new_x = start_x
        new_y = start_y

        if "right" in edge:
            new_w = max(min_w, min(max_w, start_w + delta.x()))
        elif "left" in edge:
            target_w = max(min_w, min(max_w, start_w - delta.x()))
            new_x = start_x + (start_w - target_w)
            new_w = target_w

        if "bottom" in edge:
            new_h = max(min_h, min(max_h, start_h + delta.y()))
        elif "top" in edge:
            target_h = max(min_h, min(max_h, start_h - delta.y()))
            new_y = start_y + (start_h - target_h)
            new_h = target_h

        self._has_custom_size = True
        self.container.setFixedSize(new_w, new_h)
        self.setGeometry(new_x, new_y, new_w + 32, new_h + 32)
        if hasattr(self, 'btn_close_shell'):
            self.btn_close_shell.move(new_w - 36, 8)
            self.btn_close_shell.raise_()

    def _finish_resizing(self):
        if self._dialog_key and self.container:
            try:
                settings = QSettings("MiniKick", "MiniKick")
                settings.setValue(f"dialog_size/{self._dialog_key}/width", int(self.container.width()))
                settings.setValue(f"dialog_size/{self._dialog_key}/height", int(self.container.height()))
            except Exception as e:
                logger.debug("Failed to persist dialog size: %s", e)
        self._active_resize_edge = None
        self.unsetCursor()
        if hasattr(self, 'container'):
            self.container.unsetCursor()

class ModernModal(ModernFramelessShell):
    def __init__(
        self,
        title: str = "",
        icon_path: str = "",
        icon_bg_color: str = "",
        icon_role: str = "",
        icon_color: str = "",
        width: int = 420,
        height: int | None = None,
        resizable: bool = False,
        min_width: int = 380,
        min_height: int = 320,
        dialog_key: str | None = None,
        parent=None
    ):
        super().__init__(
            width=width,
            height=height,
            resizable=resizable,
            min_width=min_width,
            min_height=min_height,
            dialog_key=dialog_key,
            parent=parent
        )
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(12)

        if icon_path:
            self._setup_header(icon_path, icon_bg_color, icon_role=icon_role, icon_color=icon_color)
        
        if title:
            self.title_lbl = QLabel(title)
            self.title_lbl.setProperty("role", "h2")
            self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.title_lbl.setWordWrap(True)
            self.content_layout.addWidget(self.title_lbl)

    def _setup_header(self, icon_path: str, bg_color: str, icon_role: str = "", icon_color: str = ""):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_container.setFixedSize(52, 52)
        
        role_dispatch = {
            COLOR_RED: ("danger_icon", COLOR_WHITE),
            COLOR_AMBER: ("warning_icon", COLOR_BLACK),
            COLOR_BLUE: ("info_icon", COLOR_WHITE),
            COLOR_GREEN: ("accent_icon", COLOR_BLACK),
            COLOR_TWITCH: ("twitch_icon", COLOR_WHITE),
            COLOR_YOUTUBE: ("youtube_icon", COLOR_WHITE),
            COLOR_TIKTOK: ("tiktok_icon", COLOR_BLACK),
            COLOR_BLACK: ("black_icon", COLOR_WHITE),
        }
        
        resolved_role, default_fg = role_dispatch.get(bg_color, ("accent_icon", COLOR_BLACK))
        final_role = icon_role or resolved_role
        final_fg = icon_color or default_fg
        
        icon_container.setProperty("role", final_role)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        from frontend.common import get_pixmap_colored
        dpr = self.devicePixelRatio()
        pixmap = get_pixmap_colored(icon_path, color_str=final_fg, size=36, dpr=dpr)
        if pixmap.isNull():
            pixmap = QIcon(icon_path).pixmap(QSize(36, 36), dpr)
        icon_lbl.setPixmap(pixmap)
        icon_inner_layout.addWidget(icon_lbl)

        icon_wrapper.addWidget(icon_container)
        self.content_layout.addLayout(icon_wrapper)

    def add_action_buttons(self, btn_left: QPushButton, btn_right: QPushButton, stretch_center: bool = False):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        if btn_left:
            btn_left.setAutoDefault(False)
            btn_left.setDefault(False)
            btn_layout.addWidget(btn_left)
        if stretch_center:
            btn_layout.addStretch()
        if btn_right:
            btn_right.setAutoDefault(False)
            btn_right.setDefault(False)
            btn_layout.addWidget(btn_right)
        
        self.content_layout.addSpacing(8)
        self.content_layout.addLayout(btn_layout)

class ModernWizardPanel(ModernFramelessShell):
    def __init__(
        self,
        title_steps: list[str],
        subtitle_steps: list[str],
        i18n,
        width: int = 500,
        height: int | None = None,
        resizable: bool = True,
        min_width: int = 440,
        min_height: int = 380,
        dialog_key: str | None = None,
        parent=None
    ):
        super().__init__(
            width=width,
            height=height,
            resizable=resizable,
            min_width=min_width,
            min_height=min_height,
            dialog_key=dialog_key,
            parent=parent
        )
        self.title_steps = title_steps
        self.subtitle_steps = subtitle_steps
        self.i18n = i18n
        self.current_step = 0
        self.total_steps = len(title_steps)
        
        self.panel_layout = QVBoxLayout(self.container)
        self.panel_layout.setContentsMargins(16, 16, 16, 16)
        self.panel_layout.setSpacing(14)
        
        self.lbl_step_num = QLabel()
        self.lbl_step_num.setProperty("role", "caption")
        self.panel_layout.addWidget(self.lbl_step_num)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setRange(0, self.total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setProperty("role", "wizard_progress")
        self.panel_layout.addWidget(self.progress_bar)
        self.panel_layout.addSpacing(2)
        
        self.lbl_title = QLabel()
        self.lbl_title.setProperty("role", "h2")
        self.lbl_title.setWordWrap(True)
        self.panel_layout.addWidget(self.lbl_title)
        
        self.lbl_subtitle = QLabel()
        self.lbl_subtitle.setProperty("role", "body")
        self.lbl_subtitle.setWordWrap(True)
        self.panel_layout.addWidget(self.lbl_subtitle)
        
        self.main_content = QStackedWidget()
        self.scroll_content = QScrollArea(self)
        self.scroll_content.setWidgetResizable(True)
        self.scroll_content.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_content.setWidget(self.main_content)
        self.panel_layout.addWidget(self.scroll_content, stretch=1)
        
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch()
        
        self.btn_back = QPushButton()
        self.btn_back.setProperty("role", "action_outlined")
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setAutoDefault(False)
        self.btn_back.setDefault(False)
        self.btn_back.clicked.connect(self._go_back)
        
        self.btn_next = QPushButton()
        self.btn_next.setProperty("role", "action_accent")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setAutoDefault(False)
        self.btn_next.setDefault(False)
        self.btn_next.clicked.connect(self._go_next)
        
        self.btn_layout.addWidget(self.btn_back)
        self.btn_layout.addWidget(self.btn_next)
        self.panel_layout.addLayout(self.btn_layout)

    def add_page(self, widget: QWidget):
        self.main_content.addWidget(widget)
        
    def start_wizard(self):
        self._update_step_ui()
        
    def _update_step_ui(self):
        try:
            step_tmpl = self.i18n.get("dialogs.wizard.step_indicator")
            self.lbl_step_num.setText(step_tmpl.replace("{current}", str(self.current_step + 1)).replace("{total}", str(self.total_steps)))
            self.progress_bar.setValue(self.current_step + 1)
            
            if 0 <= self.current_step < len(self.title_steps):
                self.lbl_title.setText(str(self.title_steps[self.current_step]))
            if 0 <= self.current_step < len(self.subtitle_steps):
                self.lbl_subtitle.setText(str(self.subtitle_steps[self.current_step]))
            if 0 <= self.current_step < self.main_content.count():
                self.main_content.setCurrentIndex(self.current_step)
            
            if self.current_step == 0:
                self.btn_back.setText(self.i18n.get("common.buttons.cancel"))
            else:
                self.btn_back.setText(self.i18n.get("common.buttons.back"))
                
            if self.current_step == self.total_steps - 1:
                self.btn_next.setText(self.i18n.get("common.buttons.save"))
            else:
                self.btn_next.setText(self.i18n.get("common.buttons.next"))

            self._apply_screen_constraints()
            if not self._resizable or not self._has_custom_size:
                self.adjustSize()
            else:
                self.resize(self.container.width() + 32, self.container.height() + 32)
        except Exception as e:
            logger.exception("[ModernWizardPanel] Error in _update_step_ui: %s", e)

    def _go_back(self):
        try:
            if self.current_step == 0:
                self.reject()
            else:
                self.current_step -= 1
                self._update_step_ui()
        except Exception as e:
            logger.exception("[ModernWizardPanel] Error in _go_back: %s", e)
            
    def _go_next(self):
        try:
            if not self.validate_step(self.current_step):
                return
            if self.current_step == self.total_steps - 1:
                self.accept()
            else:
                self.current_step += 1
                self._update_step_ui()
        except Exception as e:
            logger.exception("[ModernWizardPanel] Error in _go_next: %s", e)

    def validate_step(self, step_index: int) -> bool:
        return True

class ModernConfirmDialog(ModernModal):
    def __init__(self, i18n, parent=None, title_text="", body_text=""):
        super().__init__(title=title_text, icon_path=PATH_ICON_HELP, icon_bg_color=COLOR_RED, width=420, parent=parent)
        self.set_dialog_state("danger", QColor(239, 68, 68, 60))
        
        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        body_label.setMinimumHeight(60) 
        
        self.content_layout.addWidget(body_label)
        
        btn_cancel = self._create_btn(i18n.get("common.buttons.cancel"), "action_outlined", self.reject)
        btn_confirm = self._create_btn(i18n.get("common.buttons.continue"), "action_danger_border", self.accept)

        self.add_action_buttons(btn_cancel, btn_confirm, stretch_center=False)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setAutoDefault(False)
        btn.setDefault(False)
        btn.setMinimumWidth(110)
        btn.clicked.connect(callback)
        return btn
