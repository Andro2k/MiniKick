# backend\interfaces\instance_interfaces.py

from typing import Protocol

class SingleInstanceProvider(Protocol):    
    def is_already_running(self) -> bool: ...
    def cleanup(self) -> None: ...