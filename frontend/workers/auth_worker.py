from PySide6.QtCore import QThread, Signal
from backend.auth_manager import AuthManager

class AuthWorker(QThread):
    """Hilo dedicado exclusivamente a la autenticación (Alta Cohesión)."""
    auth_success = Signal(dict)
    auth_error = Signal(str)

    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager

    def run(self):
        try:
            # Esta llamada bloqueante ahora ocurre fuera del hilo de la UI (SoR)
            tokens = self.auth_manager.get_tokens()
            if tokens:
                self.auth_success.emit(tokens)
            else:
                self.auth_error.emit("Autorización cancelada o fallida.")
        except Exception as e:
            self.auth_error.emit(str(e))