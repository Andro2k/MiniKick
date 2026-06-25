# frontend\dialogs\visual_positioner_dialog.py

from PySide6.QtWidgets import QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from frontend.widgets.controls_component import ModernButton
from frontend.common.theme import COLOR_ACCENT, PATH_ICON_HELP
from frontend.dialogs.base_dialog import ModernModalRewards
from frontend.widgets.draggable_component import DraggableRewardsBox

class VisualPositionerDialog(ModernModalRewards):
    live_position_changed = Signal(int, int)

    def __init__(self, i18n, current_x: int, current_y: int, filepath: str, scale_val: float, parent=None):
        self.i18n = i18n
        super().__init__(
            title=self.i18n.get("rewards.dialogs.visual.title"), 
            icon_path=PATH_ICON_HELP, 
            icon_bg_color=COLOR_ACCENT, 
            width=700, 
            parent=parent
        )
        self.set_dialog_state("accent")
        
        desc_lbl = QLabel(self.i18n.get("rewards.dialogs.visual.desc"))
        desc_lbl.setProperty("role", "body")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(desc_lbl)
        self.content_layout.addSpacing(5)
        
        self.canvas_w = 640
        self.canvas_h = 360
        self.scale_factor = 1920 / self.canvas_w
        
        self.canvas_container = QFrame()
        self.canvas_container.setFixedSize(self.canvas_w, self.canvas_h)
        self.canvas_container.setObjectName("CanvasContainer")
        
        self.draggable_box = DraggableRewardsBox(self.canvas_container, self.canvas_w, self.canvas_h, self.scale_factor, filepath, scale_val)
        self.draggable_box.set_obs_coordinates(current_x, current_y)
        self.draggable_box.position_updated.connect(self.live_position_changed.emit)
        
        self.content_layout.addWidget(self.canvas_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_save = ModernButton(self.i18n.get("rewards.dialogs.visual.btn_save"), role="action_accent")
        self.btn_save.clicked.connect(self.accept)

        self.add_action_buttons(None, self.btn_save)