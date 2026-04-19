# main.py
import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication
from backend.database import iniciar_db
from frontend.gui import MiniKickMaster

if __name__ == "__main__":
    iniciar_db()
    
    # --- INICIAR SERVIDOR OBS AUTOMÁTICAMENTE ---
    # Esto lanza obs_server.py sin abrir una ventana de consola nueva
    obs_process = subprocess.Popen(
        [sys.executable, "backend/obs_server.py"],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    app = QApplication(sys.argv)
    
    # Estilos
    qss_path = os.path.join("frontend", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    gui = MiniKickMaster()
    gui.show()
    
    exit_code = app.exec()
    
    # Al cerrar la app, matamos el servidor de OBS
    obs_process.terminate()
    sys.exit(exit_code)