# backend\services\logs\__init__.py
"""Servicios para conservar registros: escritura por lotes y gestión de registros."""

from .log_writer_service import BatchedLogWriter
from .logs_service import LogService

__all__ = [
    "BatchedLogWriter",
    "LogService",
]
