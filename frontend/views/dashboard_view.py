# frontend/views/dashboard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class DashboardView(QWidget):
    # ─── CONTRATOS DE SALIDA (Inversión de Dependencias) ───
    # La vista "grita" que ocurrió una acción. No sabe ni le importa quién escucha.
    request_connection = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Encapsulamos la creación de la interfaz (Alta Cohesión)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(20)

        welcome_label = QLabel("¡Bienvenido a MiniKick!")
        welcome_label.setProperty("role", "title")
        layout.addWidget(welcome_label)

        self.btn_connect = QPushButton("Conectar a Kick")
        self.btn_connect.setProperty("role", "action_accent")
        self.btn_connect.setFixedSize(220, 45)
        self.btn_connect.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Enlazamos el clic directamente a la emisión de nuestra señal
        self.btn_connect.clicked.connect(self.request_connection.emit)
        
        layout.addWidget(self.btn_connect)

        self.status_label = QLabel("Estado: Desconectado")
        layout.addWidget(self.status_label)

        layout.addStretch()

    # ─── CONTRATOS DE ENTRADA (Separación de Responsabilidades) ───
    # Métodos expuestos para que el controlador (main) modifique la UI.
    # Así la vista no calcula la lógica, solo obedece órdenes visuales.

    def set_connecting_state(self):
        self.status_label.setText("Estado: Conectando...")
        self.status_label.setStyleSheet("") # Limpia colores previos
        self.btn_connect.setEnabled(False)

    def set_connected_state(self):
        self.status_label.setText("Estado: Conectado")
        # Usamos el color de éxito extraído de tu paleta mental de theme.py
        self.status_label.setStyleSheet("color: #51cf66;") 
        self.btn_connect.setText("¡Conectado!")
        self.btn_connect.setEnabled(False)

    def set_error_state(self, error_message: str):
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("color: #ff6b6b;") # Rojo para errores
        self.btn_connect.setEnabled(True)
        self.btn_connect.setText("Reintentar Conexión")