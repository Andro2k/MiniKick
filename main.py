import sys
import asyncio
import ctypes

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    myappid = 'minikick.app.1.0' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Importamos la UI desde nuestro nuevo archivo separado
from frontend.main_frontend import MiniKickUI
from frontend.utils import resource_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app_icon = QIcon(resource_path("icon.ico"))
    app.setWindowIcon(app_icon)

    ventana = MiniKickUI()
    ventana.show()
    
    sys.exit(app.exec())