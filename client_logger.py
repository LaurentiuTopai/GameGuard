import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(log_path="client.log",level=logging.DEBUG):
    logger = logging.getLogger("CheatGuard_IS")
    logger.setLevel(level)
    if logger.handlers:
        return logger
    
    os.makedirs(os.path.dirname(log_path) or "." , exist_ok=True)

    fh = RotatingFileHandler(log_path,maxBytes=5_000_000,backupCount=3,encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s : %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger