# frontend/components/dialogs/alert_dialogs.py

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                               QComboBox, QLineEdit, QSlider, QSpinBox, 
                               QDoubleSpinBox, QStackedWidget, QFileDialog)
from PySide6.QtCore import Qt, QPoint, Signal, QUrl
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from frontend.components.controls import ModernButton, ModernSwitch
from frontend.theme import COLOR_ACCENT, COLOR_TEXT_PRIMARY, PATH_ICON_HELP
from frontend.utils import get_icon_colored, get_assets_path
from frontend.components.dialogs.base_dialogs import ModernBaseDialog

class DraggableAlertBox(QFrame):
    """Caja arrastrable que previsualiza medios (Video/Imagen) en el lienzo virtual."""
    position_updated = Signal(int, int)

    def __init__(self, parent, canvas_w: int, canvas_h: int, scale_factor_obs: float, filepath: str, scale_val: float):
        super().__init__(parent)
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.scale_factor = scale_factor_obs 
        self.base_scale_val = scale_val
        
        self.setFixedSize(100, 100)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(83, 252, 24, 0.1); 
                border: 2px dashed #53FC18; 
                border-radius: 4px;
            }
        """)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        
        self._drag_active = False
        self._drag_offset = QPoint()

        self.media_layout = QVBoxLayout(self)
        self.media_layout.setContentsMargins(2, 2, 2, 2)
        
        if filepath and os.path.exists(filepath):
            ext = filepath.lower()
            if ext.endswith(('.mp4', '.webm')):
                self.video_widget = QVideoWidget()
                self.video_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.media_layout.addWidget(self.video_widget)

                self.player = QMediaPlayer(self)
                self.audio = QAudioOutput(self)
                self.audio.setVolume(0.0) 
                
                self.player.setAudioOutput(self.audio)
                self.player.setVideoOutput(self.video_widget)
                self.player.setSource(QUrl.fromLocalFile(filepath))
                self.player.setLoops(QMediaPlayer.Loops.Infinite)
                
                self.video_widget.videoSink().videoSizeChanged.connect(self._adjust_to_media_size)
                self.player.play()
                
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.img_lbl = QLabel()
                self.img_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.img_lbl.setScaledContents(True)
                pixmap = QPixmap(filepath)
                self.img_lbl.setPixmap(pixmap)
                self.media_layout.addWidget(self.img_lbl)
                self._adjust_to_media_size(pixmap.size())

    def _adjust_to_media_size(self, size=None):
        if size is None or type(size) == bool or not getattr(size, 'isValid', lambda: False)():
            if hasattr(self, 'video_widget') and self.video_widget.videoSink():
                size = self.video_widget.videoSink().videoSize()

        if not size or not getattr(size, 'isValid', lambda: False)() or size.width() == 0:
            return

        obs_w = size.width() * self.base_scale_val
        obs_h = size.height() * self.base_scale_val

        local_w = int(obs_w / self.scale_factor)
        local_h = int(obs_h / self.scale_factor)

        self.setFixedSize(local_w, local_h)
        x = max(0, min(self.x(), self.canvas_w - self.width()))
        y = max(0, min(self.y(), self.canvas_h - self.height()))
        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_offset = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_active:
            new_pos = self.mapToParent(event.pos()) - self._drag_offset
            x = max(0, min(new_pos.x(), self.canvas_w - self.width()))
            y = max(0, min(new_pos.y(), self.canvas_h - self.height()))
            self.move(x, y)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_active = False
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        obs_x, obs_y = self.get_obs_coordinates()
        self.position_updated.emit(obs_x, obs_y)

    def get_obs_coordinates(self) -> tuple[int, int]:
        return int(self.x() * self.scale_factor), int(self.y() * self.scale_factor)

    def set_obs_coordinates(self, obs_x: int, obs_y: int):
        local_x = int(obs_x / self.scale_factor)
        local_y = int(obs_y / self.scale_factor)
        local_x = max(0, min(local_x, self.canvas_w - self.width()))
        local_y = max(0, min(local_y, self.canvas_h - self.height()))
        self.move(local_x, local_y)

class VisualPositionerDialog(ModernBaseDialog):
    """Diálogo con el lienzo virtual 16:9 para posicionar la alerta."""
    live_position_changed = Signal(int, int)

    def __init__(self, current_x: int, current_y: int, filepath: str, scale_val: float, parent=None):
        super().__init__(title="Posicionador Visual (1920x1080)", icon_path=PATH_ICON_HELP, icon_bg_color=COLOR_ACCENT, width=700, parent=parent)
        
        desc_lbl = QLabel("Arrastra tu alerta. Al soltarla, se mostrará una vista previa en OBS.")
        desc_lbl.setProperty("role", "body")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(desc_lbl)
        self.content_layout.addSpacing(5)
        
        self.canvas_w = 640
        self.canvas_h = 360
        self.scale_factor = 1920 / self.canvas_w
        
        self.canvas_container = QFrame()
        self.canvas_container.setFixedSize(self.canvas_w, self.canvas_h)
        self.canvas_container.setStyleSheet("background-color: #0B0E11; border: 2px solid #333333; border-radius: 8px;")
        
        self.draggable_box = DraggableAlertBox(self.canvas_container, self.canvas_w, self.canvas_h, self.scale_factor, filepath, scale_val)
        self.draggable_box.set_obs_coordinates(current_x, current_y)
        self.draggable_box.position_updated.connect(self.live_position_changed.emit)
        
        self.content_layout.addWidget(self.canvas_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_save = ModernButton("Guardar y Cerrar", role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        self.add_action_buttons(self.btn_save, None)

class AlertConfigWizard(ModernBaseDialog):
    """Asistente de 2 pasos para crear o editar configuraciones de Alertas."""
    def __init__(self, parent=None, rewards_list=None, existing_config=None, existing_reward=None):
        self.is_edit_mode = existing_config is not None
        title = "Editar Alerta" if self.is_edit_mode else "Nueva Alerta"
        icon_path = get_assets_path("icons/settings.svg")
        
        super().__init__(title=title, icon_path=icon_path, icon_bg_color=COLOR_ACCENT, width=520, parent=parent)
        
        self._is_video = False
        self._build_step_indicator()
        
        self.stack = QStackedWidget()
        self.content_layout.addWidget(self.stack)

        self.step1_widget = QWidget()
        self.step2_widget = QWidget()
        
        self.stack.addWidget(self.step1_widget)
        self.stack.addWidget(self.step2_widget)
        
        self._build_step1(rewards_list, existing_reward)
        self._build_step2()
        
        if self.is_edit_mode:
            self._load_existing_data(existing_config)
        self._set_active_step(0)

    def _build_step_indicator(self):
        self.indicator_layout = QHBoxLayout()
        self.indicator_layout.setSpacing(6)
        self.indicator_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.seg1 = QFrame()
        self.seg2 = QFrame()
        
        for seg in [self.seg1, self.seg2]:
            seg.setFixedHeight(4)
            seg.setFixedWidth(40)
            seg.setStyleSheet("background-color: #333333; border-radius: 2px;")
            self.indicator_layout.addWidget(seg)
            
        self.content_layout.addLayout(self.indicator_layout)
        self.content_layout.addSpacing(10)

    def _set_active_step(self, index: int):
        self.stack.setCurrentIndex(index)
        active_style = f"background-color: {COLOR_ACCENT}; border-radius: 2px;"
        inactive_style = "background-color: #333333; border-radius: 2px;"
        
        self.seg1.setStyleSheet(active_style if index == 0 else inactive_style)
        self.seg2.setStyleSheet(active_style if index == 1 else inactive_style)

    def _build_step1(self, rewards_list, existing_reward):
        layout = QVBoxLayout(self.step1_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        header_layout = QVBoxLayout()
        header_title = QLabel("Recompensa y Archivo")
        header_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F3F4F6;")
        header_desc = QLabel("Configura qué punto de canal activará esta alerta.")
        header_desc.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_desc)
        layout.addLayout(header_layout)
        layout.addSpacing(5)
        
        lbl = QLabel("Selección de Recompensa")
        lbl.setProperty("role", "section_small")
        layout.addWidget(lbl)
        
        row1 = QHBoxLayout()
        self.combo_rewards = QComboBox()
        if rewards_list:
            self.combo_rewards.addItems(rewards_list)
        else:
            self.combo_rewards.addItem("Cargando recompensas...")
            
        if existing_reward:
            if rewards_list and existing_reward not in rewards_list:
                self.combo_rewards.addItem(existing_reward)
            self.combo_rewards.setCurrentText(existing_reward)
            
        row1.addWidget(self.combo_rewards, stretch=1)
        
        self.btn_refresh = ModernButton("", role="action_outlined")
        self.btn_refresh.setIcon(get_icon_colored("refresh.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_refresh.setToolTip("Actualizar Recompensas de Kick")
        self.btn_refresh.clicked.connect(self._request_refresh)
        row1.addWidget(self.btn_refresh)
        layout.addLayout(row1)
        
        layout.addSpacing(5)
        
        lbl2 = QLabel("Archivo Multimedia")
        lbl2.setProperty("role", "section_small")
        layout.addWidget(lbl2)
        
        row2 = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setReadOnly(True)
        self.txt_file_path.setPlaceholderText("Ej. tu_alerta.mp4 o sonido.mp3")
        
        self.btn_browse = ModernButton("Explorar", role="action_outlined")
        self.btn_browse.clicked.connect(self._browse_file)
        row2.addWidget(self.txt_file_path, stretch=1)
        row2.addWidget(self.btn_browse)
        layout.addLayout(row2)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.btn_cancel_step1 = ModernButton("Cancelar", role="action_outlined")
        self.btn_cancel_step1.clicked.connect(self.reject)
        
        self.btn_next = ModernButton("Siguiente ➔", role="action_accent")
        self.btn_next.clicked.connect(self._go_next)
        
        btn_layout.addWidget(self.btn_cancel_step1)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_next)
        layout.addLayout(btn_layout)

    def _build_step2(self):
        layout = QVBoxLayout(self.step2_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        header_layout = QVBoxLayout()
        header_title = QLabel("Ajustes de Pantalla")
        header_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F3F4F6;")
        header_desc = QLabel("Define cómo y dónde se mostrará tu alerta en el lienzo.")
        header_desc.setStyleSheet("font-size: 13px; color: #9CA3AF;")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_desc)
        layout.addLayout(header_layout)
        layout.addSpacing(5)
        
        vol_row = QHBoxLayout()
        lbl_vol = QLabel("Volumen de la alerta")
        lbl_vol.setProperty("role", "section_small")
        vol_row.addWidget(lbl_vol)
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(100)
        
        self.lbl_vol_perc = QLabel("100%")
        self.lbl_vol_perc.setProperty("role", "monospace")
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_perc.setText(f"{v}%"))
        
        vol_row.addWidget(self.slider_vol)
        vol_row.addWidget(self.lbl_vol_perc)
        layout.addLayout(vol_row)
        
        self.video_container = QWidget()
        v_layout = QVBoxLayout(self.video_container)
        v_layout.setContentsMargins(0, 10, 0, 0)
        v_layout.setSpacing(15)
        
        row_rnd = QHBoxLayout()
        lbl_rnd = QLabel("Posición Aleatoria")
        lbl_rnd.setProperty("role", "section_small")
        row_rnd.addWidget(lbl_rnd)
        
        self.chk_random_pos = ModernSwitch()
        self.chk_random_pos.toggled.connect(self._on_random_pos_toggled)
        row_rnd.addWidget(self.chk_random_pos)
        row_rnd.addStretch()
        
        self.btn_visual = ModernButton("Posicionar en OBS", role="action_outlined")
        self.btn_visual.setIcon(get_icon_colored("map-pin.svg", COLOR_TEXT_PRIMARY, 16))
        self.btn_visual.clicked.connect(self._open_visual_editor)
        row_rnd.addWidget(self.btn_visual)
        
        v_layout.addLayout(row_rnd)
        
        row_coords = QHBoxLayout()
        row_coords.addWidget(QLabel("X:"))
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-5000, 5000)
        row_coords.addWidget(self.spin_x)
        
        row_coords.addWidget(QLabel("Y:"))
        self.spin_y = QSpinBox()
        self.spin_y.setRange(-5000, 5000)
        row_coords.addWidget(self.spin_y)
        
        row_coords.addWidget(QLabel("Escala:"))
        self.spin_scale = QDoubleSpinBox()
        self.spin_scale.setRange(0.1, 5.0)
        self.spin_scale.setSingleStep(0.1)
        self.spin_scale.setValue(1.0)
        row_coords.addWidget(self.spin_scale)
        v_layout.addLayout(row_coords)
        
        layout.addWidget(self.video_container)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_back = ModernButton("🡠 Atrás", role="action_outlined")
        self.btn_back.clicked.connect(self._go_back)
        
        self.btn_save = ModernButton("Guardar Alerta", role="action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _request_refresh(self):
        if self.parent():
            self.btn_refresh.setEnabled(False)
            self.parent().refresh_rewards_requested.emit()

    def update_rewards(self, rewards_list):
        current = self.combo_rewards.currentText()
        self.combo_rewards.clear()
        self.combo_rewards.addItems(rewards_list)
        if current in rewards_list:
            self.combo_rewards.setCurrentText(current)
        self.btn_refresh.setEnabled(True)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Multimedia", "", "Media (*.mp4 *.webm *.mp3 *.wav *.ogg *.gif *.png *.jpg);;Todos (*.*)")
        if file_path:
            self.txt_file_path.setText(file_path)
            self._evaluate_media_type(file_path)

    def _evaluate_media_type(self, filepath):
        self._is_video = filepath.lower().endswith(('.mp4', '.webm', '.gif', '.png', '.jpg'))
        self.video_container.setVisible(self._is_video)
        if not self._is_video:
            self.chk_random_pos.setChecked(False)

    def _go_next(self):
        if not self.txt_file_path.text().strip():
            return
        self._set_active_step(1)

    def _go_back(self):
        self._set_active_step(0)

    def _on_random_pos_toggled(self, checked):
        self.spin_x.setEnabled(not checked)
        self.spin_y.setEnabled(not checked)
        self.btn_visual.setEnabled(not checked)

    def _open_visual_editor(self):
        filepath = self.txt_file_path.text().strip()
        if not filepath: return
        dialog = VisualPositionerDialog(self.spin_x.value(), self.spin_y.value(), filepath, self.spin_scale.value(), self)
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