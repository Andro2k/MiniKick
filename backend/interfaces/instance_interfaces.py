# backend\interfaces\instance_interfaces.py

from abc import ABC, abstractmethod

class SingleInstanceProvider(ABC):    
    @abstractmethod
    def is_already_running(self) -> bool:
        pass
    @abstractmethod
    def cleanup(self) -> None:
        pass