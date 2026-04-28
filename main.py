# main.py
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget

# Importamos tu tema global y el sidebar
from frontend.theme import GLOBAL_QSS
from frontend.sidebar import Sidebar
from frontend.views.dashboard import DashboardView # Asumo que ya creaste la vista basándonos en tu prompt anterior

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mi App - Responsive Sidebar")
        self.resize(1100, 700)
        
        # Aplicamos toda tu hoja de estilos QSS centralizada
        self.setStyleSheet(GLOBAL_QSS)

        # Widget central y layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0) 

        # Instanciamos los componentes
        self.sidebar = Sidebar()
        self.stacked_views = QStackedWidget()
        
        # Añadimos la vista del dashboard
        self.dashboard_view = DashboardView()
        self.stacked_views.addWidget(self.dashboard_view)

        # Añadimos todo al layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_views)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())