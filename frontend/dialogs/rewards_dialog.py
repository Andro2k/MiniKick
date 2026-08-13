# frontend\dialogs\rewards_dialog.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QFileDialog, QRadioButton, QButtonGroup, QPushButton, QColorDialog
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor

from frontend.widgets import ModernButton, ModernSwitch, SliderRow
from frontend.common.theme import COLOR_NEUTRAL_200, RADIUS_SM, RADIUS_MD, get_swatch_qss
from frontend.common.utils import get_icon_colored, NoWheelComboBox, NoWheelSlider
from .base_dialog import ModernWizardPanel
from .visual_positioner_dialog import VisualPositionerDialog

class RewardsConfigWizard(ModernWizardPanel):
    def __init__(self, i18n, parent=None, rewards_list=None, rewards_details_map=None, existing_config=None, existing_reward=None):
        self.i18n = i18n
        self.is_edit_mode = existing_config is not None
        self.existing_reward = existing_reward
        self.existing_config = existing_config or {}
        self.rewards_details_map = rewards_details_map or {}
        
        title_steps = [
            self.i18n.get("rewards.dialogs.wizard.step1.title"), 
            self.i18n.get("rewards.dialogs.wizard.step2.title")
        ]
        subtitle_steps = [
            self.i18n.get("rewards.dialogs.wizard.step1.desc"), 
            self.i18n.get("rewards.dialogs.wizard.step2.desc")
        ]
        super().__init__(title_steps=title_steps, subtitle_steps=subtitle_steps, i18n=i18n, width=540, parent=parent)
        self._is_video = False
        
        self._icon_refresh = get_icon_colored("refresh.svg", COLOR_NEUTRAL_200, 16)
        self._icon_map_pin = get_icon_colored("map-pin.svg", COLOR_NEUTRAL_200, 16)
        
        self.step1_widget = QWidget()
        self.step2_widget = QWidget()
        self._build_step1(rewards_list, existing_reward)
        self._build_step2()
        self.add_page(self.step1_widget)
        self.add_page(self.step2_widget)
        
        if self.is_edit_mode:
            self._load_existing_data(self.existing_config)
            
        self.start_wizard()

    def _build_color_picker(self) -> QWidget:
        color_container = QWidget()
        h_layout = QHBoxLayout(color_container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        self.btn_color_swatch = QPushButton()
        self.btn_color_swatch.setFixedSize(36, 32)
        self.btn_color_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_color_swatch.setToolTip(self.i18n.get("rewards.dialogs.wizard.step1.color_pick_tooltip"))
        self.btn_color_swatch.clicked.connect(self._open_color_dialog)

        self.txt_new_color = QLineEdit("#00e701")
        self.txt_new_color.setMaxLength(7)
        self.txt_new_color.textChanged.connect(self._on_hex_text_changed)

        h_layout.addWidget(self.btn_color_swatch)
        h_layout.addWidget(self.txt_new_color, stretch=1)

        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(4)
        preset_colors = ["#00E701", "#00F0FF", "#9146FF", "#FF4655", "#FFB800", "#FFFFFF"]
        for hex_code in preset_colors:
            btn_p = QPushButton()
            btn_p.setFixedSize(22, 22)
            btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_p.setStyleSheet(get_swatch_qss(hex_code, border_width=1, radius=RADIUS_SM))
            btn_p.clicked.connect(lambda _, c=hex_code: self._set_color(c))
            presets_layout.addWidget(btn_p)

        h_layout.addLayout(presets_layout)
        self._update_swatch_style("#00e701")
        return color_container

    def _set_color(self, hex_code: str):
        self.txt_new_color.setText(hex_code)
        self._update_swatch_style(hex_code)

    def _on_hex_text_changed(self, text: str):
        if QColor.isValidColorName(text):
            self._update_swatch_style(text)

    def _update_swatch_style(self, hex_code: str):
        self.btn_color_swatch.setStyleSheet(
            get_swatch_qss(hex_code, border_width=2, radius=RADIUS_MD)
        )

    def _open_color_dialog(self):
        current_hex = self.txt_new_color.text().strip()
        current = QColor(current_hex) if QColor.isValidColorName(current_hex) else QColor("#00e701")
        color = QColorDialog.getColor(
            current, 
            self, 
            self.i18n.get("rewards.dialogs.wizard.step1.color_pick_tooltip")
        )
        if color.isValid():
            self._set_color(color.name())

    def _build_user_input_row(self) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        
        lbl_sw = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_user_input_label"))
        lbl_sw.setProperty("role", "h3")
        
        self.chk_user_input = ModernSwitch()
        
        row.addWidget(lbl_sw)
        row.addStretch()
        row.addWidget(self.chk_user_input)
        return container

    def _build_step1(self, rewards_list, existing_reward):
        layout = QVBoxLayout(self.step1_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        if self.is_edit_mode:
            row_title_cost = QHBoxLayout()
            
            col_t = QVBoxLayout()
            lbl_edit = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.edit_title_label"))
            lbl_edit.setProperty("role", "h3")
            self.txt_edit_title = QLineEdit()
            self.txt_edit_title.setMaxLength(50)
            if existing_reward:
                self.txt_edit_title.setText(existing_reward)
            self.txt_edit_title.textChanged.connect(self._update_btn_next_state)
            col_t.addWidget(lbl_edit)
            col_t.addWidget(self.txt_edit_title)
            row_title_cost.addLayout(col_t, stretch=2)
            
            col_c = QVBoxLayout()
            lbl_c = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_cost_label"))
            lbl_c.setProperty("role", "h3")
            self.spin_edit_cost = QSpinBox()
            self.spin_edit_cost.setRange(1, 100000000)
            self.spin_edit_cost.setValue(100)
            self.spin_edit_cost.valueChanged.connect(self._update_btn_next_state)
            col_c.addWidget(lbl_c)
            col_c.addWidget(self.spin_edit_cost)
            row_title_cost.addLayout(col_c, stretch=1)
            
            layout.addLayout(row_title_cost)
            
            lbl_desc = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_desc_label"))
            lbl_desc.setProperty("role", "h3")
            layout.addWidget(lbl_desc)
            self.txt_edit_desc = QLineEdit()
            self.txt_edit_desc.setMaxLength(200)
            self.txt_edit_desc.setPlaceholderText(self.i18n.get("rewards.dialogs.wizard.step1.new_desc_placeholder"))
            layout.addWidget(self.txt_edit_desc)
            
            col_col = QVBoxLayout()
            lbl_col = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_color_label"))
            lbl_col.setProperty("role", "h3")
            col_col.addWidget(lbl_col)
            col_col.addWidget(self._build_color_picker())
            layout.addLayout(col_col)
            
            layout.addWidget(self._build_user_input_row())
        else:
            lbl_mode = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.mode_select"))
            lbl_mode.setProperty("role", "h3")
            layout.addWidget(lbl_mode)
            
            mode_row = QHBoxLayout()
            self.rb_existing = QRadioButton(self.i18n.get("rewards.dialogs.wizard.step1.mode_existing"))
            self.rb_create = QRadioButton(self.i18n.get("rewards.dialogs.wizard.step1.mode_create"))
            self.rb_existing.setChecked(True)
            
            self.btn_group_mode = QButtonGroup(self)
            self.btn_group_mode.addButton(self.rb_existing, 0)
            self.btn_group_mode.addButton(self.rb_create, 1)
            
            mode_row.addWidget(self.rb_existing)
            mode_row.addWidget(self.rb_create)
            mode_row.addStretch()
            layout.addLayout(mode_row)
            layout.addSpacing(4)
        
            self.container_existing = QWidget()
            v_existing = QVBoxLayout(self.container_existing)
            v_existing.setContentsMargins(0, 0, 0, 0)
            v_existing.setSpacing(8)
            
            lbl_ex = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.reward_selection"))
            lbl_ex.setProperty("role", "h3")
            v_existing.addWidget(lbl_ex)
            
            row1 = QHBoxLayout()
            self.combo_rewards = NoWheelComboBox()
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
            self.btn_refresh.setIcon(self._icon_refresh)
            self.btn_refresh.setIconSize(QSize(16, 16))
            self.btn_refresh.setToolTip(self.i18n.get("rewards.dialogs.wizard.step1.tooltip_refresh"))
            self.btn_refresh.clicked.connect(self._request_refresh)
            row1.addWidget(self.btn_refresh)
            v_existing.addLayout(row1)
            
            layout.addWidget(self.container_existing)
            
            self.container_create = QWidget()
            v_create = QVBoxLayout(self.container_create)
            v_create.setContentsMargins(0, 0, 0, 0)
            v_create.setSpacing(8)
            
            row_title_cost = QHBoxLayout()
            
            col_t = QVBoxLayout()
            lbl_t = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_title_label"))
            lbl_t.setProperty("role", "h3")
            self.txt_new_title = QLineEdit()
            self.txt_new_title.setMaxLength(50)
            self.txt_new_title.setPlaceholderText(self.i18n.get("rewards.dialogs.wizard.step1.new_title_placeholder"))
            col_t.addWidget(lbl_t)
            col_t.addWidget(self.txt_new_title)
            row_title_cost.addLayout(col_t, stretch=2)
            
            col_c = QVBoxLayout()
            lbl_c = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_cost_label"))
            lbl_c.setProperty("role", "h3")
            self.spin_new_cost = QSpinBox()
            self.spin_new_cost.setRange(1, 100000000)
            self.spin_new_cost.setValue(100)
            col_c.addWidget(lbl_c)
            col_c.addWidget(self.spin_new_cost)
            row_title_cost.addLayout(col_c, stretch=1)
            
            v_create.addLayout(row_title_cost)
            
            lbl_desc = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_desc_label"))
            lbl_desc.setProperty("role", "h3")
            v_create.addWidget(lbl_desc)
            self.txt_new_desc = QLineEdit()
            self.txt_new_desc.setMaxLength(200)
            self.txt_new_desc.setPlaceholderText(self.i18n.get("rewards.dialogs.wizard.step1.new_desc_placeholder"))
            v_create.addWidget(self.txt_new_desc)
            
            col_col = QVBoxLayout()
            lbl_col = QLabel(self.i18n.get("rewards.dialogs.wizard.step1.new_color_label"))
            lbl_col.setProperty("role", "h3")
            col_col.addWidget(lbl_col)
            col_col.addWidget(self._build_color_picker())
            v_create.addLayout(col_col)
            
            v_create.addWidget(self._build_user_input_row())
            
            layout.addWidget(self.container_create)
            self.container_create.setVisible(False)
            
            self.rb_existing.toggled.connect(self._on_mode_changed)
            self.rb_create.toggled.connect(self._on_mode_changed)
            self.txt_new_title.textChanged.connect(self._update_btn_next_state)
            self.spin_new_cost.valueChanged.connect(self._update_btn_next_state)
            self.combo_rewards.currentTextChanged.connect(self._on_combo_reward_changed)

        layout.addSpacing(4)
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
        
        self.txt_file_path.textChanged.connect(self._update_btn_next_state)
        
        layout.addStretch()

    def _on_combo_reward_changed(self, text: str):
        self._update_btn_next_state()
        if text and text in self.rewards_details_map:
            details = self.rewards_details_map[text]
            if "cost" in details and hasattr(self, "spin_new_cost"):
                self.spin_new_cost.setValue(int(details["cost"]))
            if "description" in details and hasattr(self, "txt_new_desc"):
                self.txt_new_desc.setText(str(details.get("description") or ""))
            if "background_color" in details and hasattr(self, "txt_new_color"):
                self._set_color(str(details.get("background_color") or "#00e701"))
            if "is_user_input_required" in details and hasattr(self, "chk_user_input"):
                self.chk_user_input.setChecked(bool(details.get("is_user_input_required", False)))

    def _on_mode_changed(self):
        is_create = hasattr(self, 'rb_create') and self.rb_create.isChecked()
        if hasattr(self, 'container_existing'):
            self.container_existing.setVisible(not is_create)
        if hasattr(self, 'container_create'):
            self.container_create.setVisible(is_create)
        self._update_btn_next_state()

    def _build_step2(self):
        layout = QVBoxLayout(self.step2_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.slider_vol = NoWheelSlider(Qt.Orientation.Horizontal)
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
        self.btn_visual.setIcon(self._icon_map_pin)
        self.btn_visual.setIconSize(QSize(16, 16))
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
        self.spin_scale.setRange(0.1, 2.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(1.0)
        row_coords.addWidget(self.spin_scale)
        v_layout.addLayout(row_coords)
        
        layout.addWidget(self.video_container)
        layout.addStretch()

    def _request_refresh(self):
        if self.parent():
            self.btn_refresh.setEnabled(False)
            self.parent().refresh_rewards_requested.emit()

    def update_rewards(self, rewards_list):
        if hasattr(self, 'combo_rewards'):
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
                
            if hasattr(self, 'btn_refresh'):
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
            reward_valid = self._is_reward_valid()
            file_valid = bool(self.txt_file_path.text().strip())
            if not reward_valid or not file_valid:
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
            
            details = self.rewards_details_map.get(self.existing_reward, {})
            
            color_val = config.get("background_color") or config.get("new_reward_data", {}).get("background_color") or details.get("background_color", "#00e701")
            self._set_color(color_val)
            
            user_in = config.get("is_user_input_required")
            if user_in is None:
                user_in = config.get("new_reward_data", {}).get("is_user_input_required")
            if user_in is None:
                user_in = details.get("is_user_input_required", False)
            if hasattr(self, 'chk_user_input'):
                self.chk_user_input.setChecked(bool(user_in))

            cost_val = config.get("cost") or config.get("new_reward_data", {}).get("cost") or details.get("cost", 100)
            if hasattr(self, 'spin_edit_cost'):
                self.spin_edit_cost.setValue(int(cost_val))

            desc_val = config.get("description") or config.get("new_reward_data", {}).get("description") or details.get("description", "")
            if hasattr(self, 'txt_edit_desc'):
                self.txt_edit_desc.setText(str(desc_val))

    def get_config_data(self):
        if self.is_edit_mode:
            reward_title = self.txt_edit_title.text().strip()
            is_create_mode = False
            new_data = None
            cost_val = self.spin_edit_cost.value()
            desc_val = self.txt_edit_desc.text().strip()
            reward_id = self.existing_config.get("id") or self.rewards_details_map.get(self.existing_reward, {}).get("id")
        else:
            is_create_mode = hasattr(self, 'rb_create') and self.rb_create.isChecked()
            if is_create_mode:
                reward_title = self.txt_new_title.text().strip()
                cost_val = self.spin_new_cost.value()
                desc_val = self.txt_new_desc.text().strip()
                new_data = {
                    "title": reward_title,
                    "cost": cost_val,
                    "description": desc_val,
                    "background_color": self.txt_new_color.text().strip() or "#00e701",
                    "is_user_input_required": self.chk_user_input.isChecked(),
                    "should_redemptions_skip_request_queue": False
                }
                reward_id = None
            else:
                reward_title = self.combo_rewards.currentText()
                details = self.rewards_details_map.get(reward_title, {})
                cost_val = details.get("cost", 100)
                desc_val = details.get("description", "")
                reward_id = details.get("id")
                new_data = None

        config = {
            "id": reward_id,
            "is_new_reward": is_create_mode,
            "new_reward_data": new_data,
            "cost": cost_val,
            "description": desc_val,
            "background_color": self.txt_new_color.text().strip() or "#00e701",
            "is_user_input_required": self.chk_user_input.isChecked() if hasattr(self, 'chk_user_input') else False,
            "filepath": self.txt_file_path.text().strip(),
            "volume": self.slider_vol.value() / 100.0,
            "scale": self.spin_scale.value() if self._is_video else 1.0,
            "pos_x": self.spin_x.value() if self._is_video else 0,
            "pos_y": self.spin_y.value() if self._is_video else 0,
            "is_random_pos": self.chk_random_pos.isChecked() if self._is_video else False
        }
        return reward_title, config

    def _is_reward_valid(self) -> bool:
        if self.is_edit_mode:
            title = self.txt_edit_title.text().strip() if hasattr(self, 'txt_edit_title') else ""
            cost = self.spin_edit_cost.value() if hasattr(self, 'spin_edit_cost') else 1
            return bool(title) and cost >= 1

        if hasattr(self, 'rb_create') and self.rb_create.isChecked():
            title = self.txt_new_title.text().strip()
            cost = self.spin_new_cost.value()
            return bool(title) and cost >= 1

        reward = self.combo_rewards.currentText().strip() if hasattr(self, 'combo_rewards') else ""
        if not reward:
            return False
            
        loading_str = self.i18n.get("rewards.dialogs.wizard.step1.loading")
        no_rewards_str = self.i18n.get("rewards.dialogs.wizard.step1.no_rewards")
        no_avail_str = self.i18n.get("rewards.dialogs.wizard.step1.no_available")
        
        if reward in (loading_str, no_rewards_str, no_avail_str):
            return False
            
        return True

    def _update_step_ui(self):
        super()._update_step_ui()
        self._update_btn_next_state()

    def _update_btn_next_state(self):
        if self.current_step == 0:
            reward_valid = self._is_reward_valid()
            file_valid = bool(self.txt_file_path.text().strip())
            self.btn_next.setEnabled(reward_valid and file_valid)
        else:
            self.btn_next.setEnabled(True)
