# frontend/components/dialogs/update_dialog.py

from PySide6.QtWidgets import (QDialog, QLabel, QHBoxLayout, QVBoxLayout, 
                               QProgressBar, QPushButton, QFrame, QGraphicsDropShadowEffect, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from frontend.theme import COLOR_ACCENT, COLOR_BG_BASE, COLOR_BG_SURFACE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY
from frontend.utils import get_icon_colored

class UpdateDialog(QDialog):
    download_requested = Signal() 
    restart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 320)
        self.version = ""

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLOR_BG_BASE};
                border: 1px solid rgba(83, 252, 24, 0.4);
                border-radius: 16px;
            }}
        """)
        
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(30)
        self.glow.setColor(QColor(83, 252, 24, 60)) 
        self.glow.setOffset(0, 0)
        self.container.setGraphicsEffect(self.glow)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(30, 30, 30, 24)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_check = QLabel()
        self.icon_check.setPixmap(get_icon_colored("circle-check.svg", COLOR_ACCENT, 48).pixmap(48, 48))
        self.icon_check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_check.setStyleSheet("border: none; background: transparent;")
        self.icon_check.hide()
        self.content_layout.addWidget(self.icon_check)

        self.lbl_top = QLabel("Buscando...")
        self.lbl_top.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_top.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        self.content_layout.addWidget(self.lbl_top)
        
        self.content_layout.addSpacing(5)

        self.lbl_title = QLabel("Actualización del Sistema")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: bold; border: none; background: transparent;")
        self.content_layout.addWidget(self.lbl_title)

        self.content_layout.addSpacing(10)

        self.lbl_subtitle = QLabel("Conectando con el servidor...")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitle.setWordWrap(True)
        self.lbl_subtitle.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 14px; border: none; background: transparent;")
        self.content_layout.addWidget(self.lbl_subtitle)

        self.content_layout.addSpacing(20)

        self.progress_container = QWidget()
        self.progress_container.setStyleSheet("border: none; background: transparent;")
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_BG_SURFACE};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_ACCENT}, stop:1 #22C55E);
                border-radius: 5px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)

        labels_layout = QHBoxLayout()
        self.lbl_prog_text = QLabel("Progreso")
        self.lbl_prog_text.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        self.lbl_prog_val = QLabel("0%")
        self.lbl_prog_val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 13px;")
        
        labels_layout.addWidget(self.lbl_prog_text)
        labels_layout.addStretch()
        labels_layout.addWidget(self.lbl_prog_val)
        progress_layout.addLayout(labels_layout)
        
        self.content_layout.addWidget(self.progress_container)
        self.progress_container.hide() 

        self.content_layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_primary = QPushButton("Reiniciar ahora")
        self.btn_primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_primary.setFixedHeight(40)
        self.btn_primary.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_TEXT_PRIMARY};
                color: {COLOR_BG_BASE};
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: #FFFFFF; }}
            QPushButton:disabled {{ background-color: {COLOR_BG_SURFACE}; color: {COLOR_TEXT_SECONDARY}; }}
        """)

        self.btn_secondary = QPushButton("Cerrar")
        self.btn_secondary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_secondary.setFixedHeight(40)
        self.btn_secondary.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLOR_BG_SURFACE};
                color: {COLOR_TEXT_PRIMARY};
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {COLOR_BG_SURFACE}; }}
        """)
        self.btn_secondary.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_primary, stretch=2)
        btn_layout.addWidget(self.btn_secondary, stretch=1)
        
        self.content_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.container)

    def show_update_available(self, version: str):
        self.version = version
        self.icon_check.hide()
        self.lbl_top.setText(f"Versión {version} disponible")
        self.lbl_title.setText("Actualización del Sistema")
        self.lbl_subtitle.setText("Se requiere un reinicio para completar la instalación.")
        self.progress_container.hide()
        
        self.btn_primary.setText("Descargar ahora")
        self.btn_primary.setEnabled(True)
        try:
            self.btn_primary.clicked.disconnect()
        except RuntimeError:
            pass
            
        self.btn_primary.clicked.connect(self.download_requested.emit)
        self.btn_secondary.show()
    def show_downloading(self):
        self.icon_check.hide()
        self.lbl_top.setText(f"Versión {self.version} disponible")
        self.lbl_title.setText("Actualización del Sistema")
        self.lbl_subtitle.setText("Descargando la nueva versión...")
        
        self.progress_bar.setValue(0)
        self.lbl_prog_val.setText("0%")
        self.progress_container.show()
        
        self.btn_primary.setText("Descargando...")
        self.btn_primary.setEnabled(False)
        self.btn_secondary.hide() 

    def update_progress(self, percentage: int):
        self.progress_bar.setValue(percentage)
        self.lbl_prog_val.setText(f"{percentage}%")

    def show_complete(self):
        self.glow.setColor(QColor(0, 0, 0, 0)) 
        self.container.setStyleSheet(f"QFrame {{ background-color: {COLOR_BG_BASE}; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; }}")
        
        self.lbl_top.hide()
        self.icon_check.show()
        self.lbl_title.setText("Actualización completada")
        self.lbl_subtitle.setText(f"Versión {self.version} instalada.")
        
        self.progress_bar.setValue(100)
        self.lbl_prog_val.setText("100%")
        
        self.btn_primary.setText("Reiniciar ahora")
        self.btn_primary.setEnabled(True)

        try:
            self.btn_primary.clicked.disconnect()
        except RuntimeError:
            pass
            
        self.btn_primary.clicked.connect(self.restart_requested.emit)
        self.btn_secondary.show()

    def show_no_update(self):
        self.glow.setColor(QColor(0, 0, 0, 0))
        self.icon_check.hide()
        self.lbl_top.hide()
        self.lbl_title.setText("Sistema Actualizado")
        self.lbl_subtitle.setText("Tu versión de MiniKick ya es la última disponible.")
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.setText("Cerrar")
        self.btn_secondary.show()

    def show_error(self, message: str):
        self.glow.setColor(QColor(239, 68, 68, 60))
        self.container.setStyleSheet(f"QFrame {{ background-color: {COLOR_BG_BASE}; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 16px; }}")
        
        self.icon_check.hide()
        self.lbl_top.setText("Error de Actualización")
        self.lbl_top.setStyleSheet("color: #EF4444; font-size: 13px; font-weight: 600; border: none; background: transparent;")
        self.lbl_title.setText("Fallo en la descarga")
        self.lbl_subtitle.setText(message)
        self.progress_container.hide()
        
        self.btn_primary.hide()
        self.btn_secondary.show()