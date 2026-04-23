import sys
import os
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from backend.database import iniciar_db
from frontend.gui import MiniKickMaster

# Definir la raíz del proyecto para rutas absolutas y seguras multiplataforma
BASE_DIR = Path(__file__).resolve().parent

def configurar_icono_windows():
    """Evita que Windows muestre el ícono de Python genérico en la barra de tareas."""
    if os.name == 'nt':
        import ctypes
        myappid = 'theandro2k.minikick.studio.0.3'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def iniciar_servidor_obs():
    """Inicia el servidor de OBS en un proceso secundario de forma invisible."""
    obs_script = BASE_DIR / "backend" / "obs_server.py"
    
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    
    # Pasamos la ruta absoluta del script convertido a string
    return subprocess.Popen(
        [sys.executable, str(obs_script)],
        creationflags=creationflags
    )

def main():
    """Punto de entrada principal de la aplicación."""
    iniciar_db()
    configurar_icono_windows()
    
    # Iniciamos el proceso en segundo plano
    obs_process = iniciar_servidor_obs()
    
    try:
        app = QApplication(sys.argv)
        
        # 1. Configurar el Ícono Global
        icon_path = BASE_DIR / "icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        
        # 2. Cargar Estilos QSS
        qss_path = BASE_DIR / "frontend" / "style.qss"
        if qss_path.exists():
            # pathlib permite leer el archivo directamente sin necesidad de usar 'open'
            app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

        # 3. Iniciar la Interfaz Gráfica
        gui = MiniKickMaster()
        
        # Reforzamos el ícono en la ventana principal
        if icon_path.exists():
            gui.setWindowIcon(QIcon(str(icon_path)))
        
        gui.show()
        
        # Ejecutar el bucle de eventos de PyQt6
        exit_code = app.exec()
        sys.exit(exit_code)
        
    finally:
        # GARANTÍA DE CIERRE: Esto se ejecuta SIEMPRE, incluso si la app crashea
        if obs_process:
            print("[*] Cerrando el servidor de OBS en segundo plano...")
            obs_process.terminate()
            obs_process.wait() # Esperamos a que el sistema operativo libere el proceso

if __name__ == "__main__":
    main()