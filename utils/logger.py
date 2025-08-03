# utils/logger.py

import logging
import os

from logging.handlers import RotatingFileHandler
from utils.config import LOG_DIR, LOG_LEVEL


def setup_logger(name: str, log_file: str, level=logging.DEBUG) -> logging.Logger:
    """
    Create and configure a rotating logger.

    Args:
        name (str): Logger name.
        log_file (str): File name for the log.
        level (int): Logging level.

    Returns:
        Logger: Configured rotating logger.
    """
    filepath = os.path.join(LOG_DIR, log_file)

    handler = RotatingFileHandler(filepath, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    chandler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    chandler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(chandler)
    logger.propagate = False  # Prevent double logging on console

    return logger


# Loggers with rotation
bot_logger = setup_logger("bot", "bot.log", level=logging.getLevelNamesMapping().get(LOG_LEVEL, logging.INFO))
service_logger = setup_logger("services", "services.log", level=logging.getLevelNamesMapping().get(LOG_LEVEL, logging.INFO))
error_logger = setup_logger("errors", "errors.log", level=logging.ERROR)
