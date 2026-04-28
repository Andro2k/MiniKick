from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1A1A1A; color: white;")
        
        # Layout principal de la vista
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_icon = QLabel("⊞") # Icono temporal
        header_icon.setStyleSheet("color: #888888; font-size: 18px;")
        header_title = QLabel("Dashboard")
        header_title.setStyleSheet("color: #888888; font-size: 16px; font-weight: bold;")
        
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- Título de bienvenida ---
        welcome_label = QLabel("Welcome back John Doe!")
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 10px; margin-bottom: 20px;")
        layout.addWidget(welcome_label)

        # --- Grid de Tarjetas (Cards) ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # Crear tarjetas de ejemplo (los rectángulos oscuros)
        card1 = self.create_card()
        card2 = self.create_card()
        card3 = self.create_card()
        card4 = self.create_card()

        # Añadir al grid (fila, columna)
        grid_layout.addWidget(card1, 0, 0)
        grid_layout.addWidget(card2, 0, 1)
        grid_layout.addWidget(card3, 1, 0, 1, 2) # Ocupa 2 columnas
        grid_layout.addWidget(card4, 2, 0, 1, 2)

        layout.addLayout(grid_layout)
        layout.addStretch() # Empuja todo hacia arriba

    def create_card(self):
        card = QFrame()
        card.setMinimumHeight(150)
        # Estilo de las tarjetas simulando el de tu imagen
        card.setStyleSheet("""
            QFrame {
                background-color: #222222;
                border-radius: 12px;
                border: 1px solid #333333;
            }
        """)
        return card