# frontend/views/points.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from frontend.theme import Palette

class PointsView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        titulo = QLabel("Gestión de Puntos de Canal")
        titulo.setObjectName("h1")
        
        info = QLabel("Aquí implementaremos la lógica para escuchar recompensas y automatizar acciones.")
        info.setObjectName("subtitle")
        info.setWordWrap(True)
        
        layout.addWidget(titulo)
        layout.addWidget(info)
        layout.addStretch()