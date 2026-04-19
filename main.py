import sys
import os
from PyQt6.QtWidgets import QApplication
from backend.database import iniciar_db
from frontend.gui import MiniKickGUI

if __name__ == "__main__":
    # 1. Asegurar que la tabla en minikick.db exista antes de abrir la app
    iniciar_db()
    
    # 2. Iniciar la aplicación gráfica
    app = QApplication(sys.argv)
    
    # Cargar estilos si existen
    qss_path = os.path.join("frontend", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    # 3. Mostrar la ventana principal
    gui = MiniKickGUI()
    gui.show()
    sys.exit(app.exec())