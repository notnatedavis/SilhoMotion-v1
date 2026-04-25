# utils/logger.py

# ----- Imports -----
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ----- Constants -----
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ----- Main -----
def setup_logger(name: str, log_file: str = "logs/project.log", level=logging.DEBUG) -> logging.Logger :
    # configure and return a logger with console and rotating file handlers
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # console handler (INFO and above)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # file handler (5 MB rotation, 2 backups)
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(fh)

    return logger