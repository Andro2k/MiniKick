import logging
from PySide6.QtCore import QObject, Signal

class LogEmitter(QObject):
    """Objeto QObject necesario para emitir señales, ya que logging.Handler no lo es."""
    log_received = Signal(str, str)  # (Nivel, Mensaje Formateado)

class QLogHandler(logging.Handler):
    """
    Captura los logs estándar de Python y los emite como señales de PySide6.
    """
    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()
        
        # Formato estándar del log
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        # Evita que el formateo bloquee o rompa si hay caracteres extraños
        try:
            msg = self.format(record)
            self.emitter.log_received.emit(record.levelname, msg)
        except Exception:
            self.handleError(record)

class StreamToLogger:
    """
    Interviene sys.stdout y sys.stderr.
    Cualquier print() o error fatal de Python se redirige aquí.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        # Evita procesar líneas vacías que causan saltos de línea extra
        for line in buf.rstrip().splitlines():
            if line.strip():
                self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        """Requerido por la interfaz de sys.stdout/stderr"""
        pass