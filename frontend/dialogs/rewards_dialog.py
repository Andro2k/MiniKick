# frontend\dialogs\rewards_dialogs.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QLineEdit, QSlider, QSpinBox, 
                               QDoubleSpinBox, QFileDialog)
from PySide6.QtCore import Qt

from frontend.widgets.controls_component import ModernButton, ModernSwitch
from frontend.common.theme import COLOR_TEXT_PRIMARY
from frontend.common.utils import get_icon_colored
from frontend.dialogs.base_dialog import ModernWizardPanel
from frontend.widgets.blocks_component import SliderRow
from frontend.dialogs.visual_positioner_dialog import VisualPositionerDialog

class RewardsConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, rewards_list=None, existing_config=None, existing_reward=None):
        self.i18n = i18n
        self.is_edit_mode = existing_config is not None
        self.existing_reward = existing_reward
        
        title_steps = [
            self.i18n.get("rewards.dialogs.wizard.step1.title"),
            self.i18n.get("rewards.dialogs.wizard.step2.title")
        ]
        subtitle_steps = [
            self.i18n.get("rewards.dialogs.wizard.step1.desc"),
            self.i18n.get("rewards.dialogs.wizard.step2.desc")
        ]
        
        super().__init__(
            title_steps=title_steps,
            subtitle_steps=subtitle_steps,
            i18n=i18n,
            width=520,
            parent=parent
        )
        
        self._is_video = False
        
        self.step1_widget = QWidget()
        self.step2_widget = QWidget()
        
        self._build_step1(rewards_list, existing_reward)
        self._build_step2()
        
        self.add_page(self.step1_widget)
        self.add_page(self.step2_widget)
        
        if self.is_edit_mode:
            self._load_existing_data(existing_config)
            
        self.start_wizard()

    def _build_step1(self, rewards_list, existing_reward):
        layout = QVBoxLayout(self.step1_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        lbl = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.reward_selection"))
        lbl.setProperty("role", "h3")
        layout.addWidget(lbl)
        
        row1 = QHBoxLayout()
        self.combo_rewards = QComboBox()
        if rewards_list:
            self.combo_rewards.addItems(rewards_list)
        else:
            self.combo_rewards.addItem(self.i18n.get("rewards.dialogs.wizard.step1.loading"))
            
        if existing_reward:
            if rewards_list and existing_reward not in rewards_list:
                self.combo_rewards.addItem(existing_reward)
            self.combo_rewards.setCurrentText(existing_reward)
            
        row1.addWidget(self.combo_rewards, stretch=1)
        
        self.btn_refresh = ModernButton("", role="action_neutral_border")
        self.btn_refresh.setIcon(get_icon_colored("refresh.svg", COLOR_TEXT_PRIMARY, 24))
        self.btn_refresh.setToolTip(self.i18n.get("rewards.dialogs.wizard.step1.tooltip_refresh"))
        self.btn_refresh.clicked.connect(self._request_refresh)
        row1.addWidget(self.btn_refresh)
        layout.addLayout(row1)
        
        layout.addSpacing(5)
        
        lbl2 = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.file_label"))
        lbl2.setProperty("role", "h3")
        layout.addWidget(lbl2)
        
        row2 = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setReadOnly(True)
        self.txt_file_path.setPlaceholderText(self.i18n.get("rewards.dialogs.wizard.step1.file_placeholder"))
        
        self.btn_browse = ModernButton(self.i18n.get("common.buttons.browse"), role="action_neutral_border")
        self.btn_browse.clicked.connect(self._browse_file)
        row2.addWidget(self.txt_file_path, stretch=1)
        row2.addWidget(self.btn_browse)
        layout.addLayout(row2)
        
        layout.addStretch()
        
        layout.addStretch()

    def _build_step2(self):
        layout = QVBoxLayout(self.step2_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "monospace")
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_perc.setText(f"{v}%"))
        
        vol_row = SliderRow(
            icon_name="volume.svg",
            title_text=self.i18n.get("rewards.dialogs.wizard.step2.volume"),
            desc_text="",
            slider_widget=self.slider_vol,
            value_label=self.lbl_vol_perc
        )
        layout.addWidget(vol_row)
        
        self.video_container = QWidget()
        v_layout = QVBoxLayout(self.video_container)
        v_layout.setContentsMargins(0, 10, 0, 0)
        v_layout.setSpacing(15)
        
        row_rnd = QHBoxLayout()
        lbl_rnd = QLabel(self.i18n.get("rewards.dialogs.wizard.step2.random_pos"))
        lbl_rnd.setProperty("role", "h3")
        row_rnd.addWidget(lbl_rnd)
        
        self.chk_random_pos = ModernSwitch()
        self.chk_random_pos.toggled.connect(self._on_random_pos_toggled)
        row_rnd.addWidget(self.chk_random_pos)
        row_rnd.addStretch()
        
        self.btn_visual = ModernButton(self.i18n.get("rewards.dialogs.wizard.step2.btn_visual"), role="action_neutral_border")
        self.btn_visual.setIcon(get_icon_colored("map-pin.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_visual.clicked.connect(self._open_visual_editor)
        row_rnd.addWidget(self.btn_visual)
        
        v_layout.addLayout(row_rnd)
        
        row_coords = QHBoxLayout()
        row_coords.addWidget(QLabel(self.i18n.get("rewards.dialogs.wizard.step2.coord_x")))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-5000, 5000)
        row_coords.addWidget(self.spin_x)
        
        row_coords.addWidget(QLabel(self.i18n.get("rewards.dialogs.wizard.step2.coord_y")))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(-5000, 5000)
        row_coords.addWidget(self.spin_y)
        
        row_coords.addWidget(QLabel(self.i18n.get("rewards.dialogs.wizard.step2.scale")))
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 5.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(1.0)
        row_coords.addWidget(self.spin_scale)
        v_layout.addLayout(row_coords)
        
        layout.addWidget(self.video_container)
        layout.addStretch()

        layout.addStretch()

    def _request_refresh(self):
        if self.parent():
            self.btn_refresh.setEnabled(False)
            self.parent().refresh_rewards_requested.emit()

    def update_rewards(self, rewards_list):
        current = self.combo_rewards.currentText()
        self.combo_rewards.clear()
        if hasattr(self, 'existing_reward') and self.existing_reward:
            if self.existing_reward not in rewards_list:
                rewards_list.insert(0, self.existing_reward)
        self.combo_rewards.addItems(rewards_list)
        if current in rewards_list:
            self.combo_rewards.setCurrentText(current)
        elif hasattr(self, 'existing_reward') and self.existing_reward in rewards_list:
            self.combo_rewards.setCurrentText(self.existing_reward)
            
        self.btn_refresh.setEnabled(True)

    def _browse_file(self):
        title = self.i18n.get("rewards.dialogs.wizard.file_dialog_title")
        filter_str = self.i18n.get("rewards.dialogs.wizard.file_dialog_filter")
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if file_path:
            self.txt_file_path.setText(file_path)
            self._evaluate_media_type(file_path)

    def _evaluate_media_type(self, filepath):
        self._is_video = filepath.lower().endswith(('.mp4', '.webm', '.gif', '.png', '.jpg'))
        self.video_container.setVisible(self._is_video)
        if not self._is_video:
            self.chk_random_pos.setChecked(False)

    def _on_random_pos_toggled(self, checked):
        self.spin_x.setEnabled(not checked)
        self.spin_y.setEnabled(not checked)
        self.btn_visual.setEnabled(not checked)

    def validate_step(self, step_index: int) -> bool:
        if step_index == 0:
            if not self.txt_file_path.text().strip():
                return False
        return True

    def _open_visual_editor(self):
        filepath = self.txt_file_path.text().strip()
        if not filepath: return
        dialog = VisualPositionerDialog(self.i18n, self.spin_x.value(), self.spin_y.value(), filepath, self.spin_scale.value(), self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.spin_x.setValue(dialog.draggable_box.get_obs_coordinates()[0])
            self.spin_y.setValue(dialog.draggable_box.get_obs_coordinates()[1])
            if hasattr(dialog.draggable_box, 'player'):
                dialog.draggable_box.player.stop()

    def _load_existing_data(self, config):
        filepath = config if isinstance(config, str) else config.get("filepath", "")
        self.txt_file_path.setText(filepath)
        self._evaluate_media_type(filepath)
        if isinstance(config, dict):
            self.spin_x.setValue(config.get("pos_x", 0))
            self.spin_y.setValue(config.get("pos_y", 0))
            self.spin_scale.setValue(config.get("scale", 1.0))
            
            vol_val = int(config.get("volume", 1.0) * 100)
            self.slider_vol.setValue(vol_val)
            self.lbl_vol_perc.setText(f"{vol_val}%")
            
            self.chk_random_pos.setChecked(config.get("is_random_pos", False))

    def get_config_data(self):
        reward = self.combo_rewards.currentText()
        config = {
            "filepath": self.txt_file_path.text().strip(),
            "volume": self.slider_vol.value() / 100.0,
            "scale": self.spin_scale.value() if self._is_video else 1.0,
            "pos_x": self.spin_x.value() if self._is_video else 0,
            "pos_y": self.spin_y.value() if self._is_video else 0,
            "is_random_pos": self.chk_random_pos.isChecked() if self._is_video else False
        }
        return reward, config