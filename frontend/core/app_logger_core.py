# frontend\core\app_logger_core.py

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
from frontend.common.log_handler import QLogHandler, StreamToLogger

def setup_application_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) 
    
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        
    q_log_handler = QLogHandler()
    logger.addHandler(q_log_handler)
    
    app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
    log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'minikick.log')
    
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7, 
        encoding='utf-8'
    )
    
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)   
    logger.addHandler(file_handler)
    
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("cloudscraper").setLevel(logging.WARNING)
    logging.getLogger("comtypes").setLevel(logging.WARNING)

    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
    except Exception:
        pass
    
    return logger, q_log_handler
