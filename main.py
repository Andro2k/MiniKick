# main.py
import sys
import os
import subprocess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon  # <-- 1. Importar QIcon

from backend.database import iniciar_db
from frontend.gui import MiniKickMaster

if __name__ == "__main__":
    iniciar_db()
    
    # --- FIX PARA LA BARRA DE TAREAS EN WINDOWS ---
    # Esto evita que Windows muestre el ícono de Python genérico en lugar del tuyo
    if os.name == 'nt':
        import ctypes
        myappid = 'theandro2k.minikick.studio.0.3' # Identificador único de tu app
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # --- INICIAR SERVIDOR OBS AUTOMÁTICAMENTE ---
    obs_process = subprocess.Popen(
        [sys.executable, "backend/obs_server.py"],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )
    
    app = QApplication(sys.argv)
    
    # --- 2. CONFIGURAR EL ÍCONO GLOBAL ---
    # Usamos os.path.abspath para asegurar que siempre encuentre el archivo
    # sin importar desde dónde ejecutes el script.
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "icon.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Estilos
    qss_path = os.path.join("frontend", "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    gui = MiniKickMaster()
    # Opcional: También puedes forzar el ícono específicamente en la ventana principal
    if os.path.exists(icon_path):
        gui.setWindowIcon(QIcon(icon_path))
    
    gui.show()
    
    exit_code = app.exec()
    
    # Al cerrar la app, matamos el servidor de OBS
    obs_process.terminate()
    sys.exit(exit_code)