# backend\connections\__init__.py

from .worker_shutdown import WorkerShutdownCoordinator, is_worker_running
from .worker_slot import WorkerSlot

__all__ = [
    "WorkerShutdownCoordinator",
    "WorkerSlot",
    "is_worker_running",
]
