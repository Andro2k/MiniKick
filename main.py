# main.py
import sys
from PySide6.QtWidgets import QApplication
from dotenv import load_dotenv

# Importamos el orquestador y el estilo
from frontend.main_window import MainWindow
from frontend.theme import GLOBAL_QSS

def bootstrap():
    """
    Configura el entorno antes de lanzar la interfaz.
    Sigue la regla de Separación de Responsabilidades: 
    el inicio está aislado de la lógica.
    """
    # 1. Cargar variables de entorno del archivo .env
    load_dotenv()

    # 2. Crear la aplicación Qt
    app = QApplication(sys.argv)

    # 3. Aplicar la hoja de estilos global (QSS)
    # Esto asegura que toda la app herede el diseño de theme.py
    app.setStyleSheet(GLOBAL_QSS)

    # 4. Instanciar y mostrar la ventana principal (El Controlador)
    window = MainWindow()
    window.show()

    # 5. Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    bootstrap()