# frontend/components/dialogs.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar, QSizePolicy
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent
import os
from PySide6.QtCore import QPoint, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from frontend.theme import COLOR_ACCENT, PATH_ICON_HELP, PATH_ICON_UPDATE

# ─── 1. CLASE BASE (Abstracción Estructural - SoR & DRY) ──────────────────────
class ModernBaseDialog(QDialog):
    """Provee la estructura visual base inspirada en el diseño centrado."""
    
    def __init__(self, icon_path: str, icon_bg_color: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        self.container = QFrame()
        self.container.setObjectName("SquareDialog")
        self.container.setFixedWidth(420)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(32, 32, 32, 32)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self._setup_header(icon_path, icon_bg_color)
        self.main_layout.addWidget(self.container)

    def _setup_header(self, icon_path: str, bg_color: str):
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_container = QFrame()
        icon_size = 52
        icon_container.setFixedSize(icon_size, icon_size)
        role = "danger_icon" if bg_color == "#EF4444" else "accent_icon"
        icon_container.setProperty("dialog_role", role)
        
        icon_inner_layout = QVBoxLayout(icon_container)
        icon_inner_layout.setContentsMargins(0, 0, 0, 0)
        icon_inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(icon_path).pixmap(24, 24))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_inner_layout.addWidget(icon_lbl)

        icon_wrapper.addWidget(icon_container)
        
        self.content_layout.addLayout(icon_wrapper)
        self.content_layout.addSpacing(8) 

    def add_action_buttons(self, btn_primary: QPushButton, btn_secondary: QPushButton):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if btn_primary: btn_layout.addWidget(btn_primary)
        if btn_secondary: btn_layout.addWidget(btn_secondary)
        
        self.content_layout.addSpacing(16)
        self.content_layout.addLayout(btn_layout)


# ─── 2. IMPLEMENTACIONES ESPECÍFICAS (Alta Cohesión) ──────────────────────────
class ModernConfirmDialog(ModernBaseDialog):
    
    def __init__(self, parent=None, title_text="Desvincular Cuenta", body_text="¿Estás seguro de que deseas continuar? Esta acción no se puede deshacer."):
        super().__init__(PATH_ICON_HELP, "#EF4444", parent)
        self.setWindowTitle(title_text)
        
        title_lbl = QLabel(title_text)
        title_lbl.setProperty("role", "title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setWordWrap(True)
        self.content_layout.addWidget(title_lbl)

        body_label = QLabel(body_text)
        body_label.setProperty("role", "body")
        body_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_label.setWordWrap(True)
        # Política para asegurar que empuje el layout hacia abajo en lugar de cortarse
        body_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content_layout.addWidget(body_label)

        self.btn_confirm = self._create_btn("Continuar", "action_danger", self.accept)
        self.btn_cancel = self._create_btn("Cancelar", "action_outlined", self.reject)
        self.add_action_buttons(self.btn_confirm, self.btn_cancel)

    def _create_btn(self, text, role, callback):
        btn = QPushButton(text)
        btn.setProperty("role", role)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumWidth(120)
        btn.clicked.connect(callback)
        return btn


class UpdateDialog(ModernBaseDialog):
    download_requested = Signal() 

    def __init__(self, parent=None):
        super().__init__(PATH_ICON_UPDATE, COLOR_ACCENT, parent)
        self.setWindowTitle("Actualización del Sistema")
        
        self.title_lbl = QLabel("Buscando Actualizaciones")
        self.title_lbl.setProperty("role", "title")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.title_lbl)

        self.status_label = QLabel("Conectando con el servidor...")
        self.status_label.setProperty("role", "status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content_layout.addWidget(self.status_label)

        pb_layout = QHBoxLayout()
        pb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("UpdateProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedWidth(280)
        sp = self.progress_bar.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.progress_bar.setSizePolicy(sp)
        
        pb_layout.addWidget(self.progress_bar)
        self.content_layout.addSpacing(10)
        self.content_layout.addLayout(pb_layout)

        self.action_button = QPushButton("Descargar e Instalar")
        self.action_button.setProperty("role", "action_accent")
        self.action_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_button.setMinimumWidth(160)
        self.action_button.setVisible(False)
        self.action_button.clicked.connect(self.download_requested.emit)

        self.btn_close = QPushButton("Cancelar")
        self.btn_close.setProperty("role", "action_outlined")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setMinimumWidth(120)
        self.btn_close.clicked.connect(self.reject)

        self.add_action_buttons(self.action_button, self.btn_close)

    def show_update_available(self, version: str):
        self.title_lbl.setText("Actualización Disponible")
        self.status_label.setText(f"¡Nueva versión {version} está lista para descargar!")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.action_button.setVisible(True) 
        self.btn_close.setText("Quizás luego")

    def show_downloading(self):
        self.title_lbl.setText("Descargando Actualización")
        self.status_label.setText("Por favor espera, no cierres la aplicación.")
        self.progress_bar.setRange(0, 0) 
        self.action_button.setEnabled(False)
        self.btn_close.setVisible(False) 

    def show_no_update(self):
        self.title_lbl.setText("Sistema Actualizado")
        self.status_label.setText("Tu versión de MiniKick ya es la última disponible.")
        self.progress_bar.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setProperty("role", "action_accent")
        self.btn_close.style().unpolish(self.btn_close)
        self.btn_close.style().polish(self.btn_close)

    def show_error(self, message: str):
        self.title_lbl.setText("Error de Actualización")
        self.status_label.setText(f"Ocurrió un fallo: {message}")
        self.progress_bar.hide()
        self.action_button.setVisible(False)
        self.btn_close.setText("Cerrar")
        self.btn_close.setVisible(True)
        self.btn_close.setEnabled(True)

class DraggableAlertBox(QFrame):
    """Componente que representa el video arrastrable con previsualización real."""
    def __init__(self, parent, canvas_w: int, canvas_h: int, scale_factor_obs: float, filepath: str, scale_val: float):
        super().__init__(parent)
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.scale_factor = scale_factor_obs 
        
        # Tamaño simulado (Asumimos alerta base de 300px escalada por el multiplicador del usuario)
        base_obs_size = 300 * scale_val
        local_size = int(base_obs_size / self.scale_factor)
        self.setFixedSize(local_size, local_size)
        
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

        # ─── MOTOR MULTIMEDIA (Previsualización en vivo) ───
        self.media_layout = QVBoxLayout(self)
        self.media_layout.setContentsMargins(2, 2, 2, 2)
        
        if filepath and os.path.exists(filepath):
            ext = filepath.lower()
            if ext.endswith(('.mp4', '.webm')):
                self.video_widget = QVideoWidget()
                # Evita que el reproductor robe los eventos del ratón para poder arrastrarlo
                self.video_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.media_layout.addWidget(self.video_widget)

                self.player = QMediaPlayer(self)
                self.audio = QAudioOutput(self)
                self.audio.setVolume(0.0) # Silenciado estrictamente
                
                self.player.setAudioOutput(self.audio)
                self.player.setVideoOutput(self.video_widget)
                self.player.setSource(QUrl.fromLocalFile(filepath))
                self.player.setLoops(QMediaPlayer.Loops.Infinite) # Bucle infinito
                self.player.play()
                
            elif ext.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.img_lbl = QLabel()
                self.img_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                self.img_lbl.setScaledContents(True)
                self.img_lbl.setPixmap(QPixmap(filepath))
                self.media_layout.addWidget(self.img_lbl)

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

    def get_obs_coordinates(self) -> tuple[int, int]:
        return int(self.x() * self.scale_factor), int(self.y() * self.scale_factor)

    def set_obs_coordinates(self, obs_x: int, obs_y: int):
        local_x = int(obs_x / self.scale_factor)
        local_y = int(obs_y / self.scale_factor)
        local_x = max(0, min(local_x, self.canvas_w - self.width()))
        local_y = max(0, min(local_y, self.canvas_h - self.height()))
        self.move(local_x, local_y)

class VisualPositionerDialog(ModernBaseDialog):
    def __init__(self, current_x: int, current_y: int, filepath: str, scale_val: float, parent=None):
        super().__init__(PATH_ICON_HELP, COLOR_ACCENT, parent)
        self.setWindowTitle("Posicionador Visual (1920x1080)")
        self.container.setFixedWidth(700)
        
        desc_lbl = QLabel("Arrastra tu alerta para establecer en qué parte de la pantalla aparecerá.")
        desc_lbl.setProperty("role", "body")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(desc_lbl)
        self.content_layout.addSpacing(10)
        
        self.canvas_w = 640
        self.canvas_h = 360
        self.scale_factor = 1920 / self.canvas_w
        
        self.canvas_container = QFrame()
        self.canvas_container.setFixedSize(self.canvas_w, self.canvas_h)
        self.canvas_container.setStyleSheet("background-color: #0B0E11; border: 2px solid #333333; border-radius: 8px;")
        
        # Pasamos el archivo de video y la escala al constructor
        self.draggable_box = DraggableAlertBox(self.canvas_container, self.canvas_w, self.canvas_h, self.scale_factor, filepath, scale_val)
        self.draggable_box.set_obs_coordinates(current_x, current_y)
        
        self.content_layout.addWidget(self.canvas_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_save = QPushButton("Guardar Posición")
        self.btn_save.setProperty("role", "action_accent")
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setProperty("role", "action_outlined")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.add_action_buttons(self.btn_save, self.btn_cancel)
        
    def get_final_positions(self) -> tuple[int, int]:
        return self.draggable_box.get_obs_coordinates()