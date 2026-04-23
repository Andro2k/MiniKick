# frontend/gui.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget
from frontend.theme import get_sheet

# Importar el Sidebar y las Vistas
from frontend.components.sidebar import Sidebar
from frontend.views.dashboard import DashboardView
from frontend.views.points import PointsView

class MiniKickMaster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniKick v0.3 - Studio")
        self.setMinimumSize(720, 500) # Más ancha para acomodar el sidebar
        
        # Aplicamos el QSS global
        self.setStyleSheet(get_sheet())
        
        # Widget Central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout Principal Horizontal (Sidebar Izquierda + Contenido Derecha)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Instanciar Sidebar
        self.sidebar = Sidebar()
        self.main_layout.addWidget(self.sidebar)

        # 2. Instanciar StackedWidget (El contenedor de páginas)
        self.pages = QStackedWidget()
        self.main_layout.addWidget(self.pages, 1) # El "1" hace que ocupe el resto del espacio

        # 3. Crear e inyectar las vistas
        self.view_dashboard = DashboardView()
        self.view_points = PointsView()

        self.pages.addWidget(self.view_dashboard) # Index 0
        self.pages.addWidget(self.view_points)    # Index 1

        # 4. Conectar la señal del sidebar para cambiar la página
        self.sidebar.page_changed.connect(self.pages.setCurrentIndex)

    def closeEvent(self, event):
        """Se ejecuta al intentar cerrar la ventana."""
        # Si el bot está activo en el dashboard, lo detenemos limpiamente
        if hasattr(self, 'view_dashboard') and self.view_dashboard.bot_activo:
            self.view_dashboard.stop_bot()
        
        event.accept()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniKickMaster()
    window.show()
    sys.exit(app.exec())