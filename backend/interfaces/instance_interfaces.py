from abc import ABC, abstractmethod

class SingleInstanceProvider(ABC):
    """Interfaz para gestionar la ejecución de una única instancia de la app."""
    
    @abstractmethod
    def is_already_running(self) -> bool:
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        pass