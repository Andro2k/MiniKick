import socket
import logging
from backend.interfaces.instance_interfaces import SingleInstanceProvider

class SocketInstanceProvider(SingleInstanceProvider):
    """
    Implementación que utiliza el enlace a un puerto local para 
    garantizar que solo exista una instancia activa.
    """
    def __init__(self, port: int = 45678):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def is_already_running(self) -> bool:
        try:
            # Intentamos adueñarnos del puerto
            self.sock.bind(("127.0.0.1", self.port))
            return False 
        except socket.error:
            # Si el puerto ya está en uso, otra instancia está corriendo
            return True

    def cleanup(self) -> None:
        try:
            self.sock.close()
        except Exception as e:
            logging.error(f"Error limpiando el socket de instancia: {e}")