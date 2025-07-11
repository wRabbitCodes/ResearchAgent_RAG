import logging
from logging.handlers import RotatingFileHandler
import os

from src.config.config import Config


def setup_logger():
    config = Config()
    os.makedirs(config.log_dir, exist_ok=True)
    os.chmod(config.log_dir, 0o775)  # grant permission

    log_file = os.path.join(config.log_dir, "app.log")
    try:
        handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5
        )  # 5MB per file, keep 5 backups
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
    except PermissionError as e:
        logging.error(f"Failed to set up file logger: {e}")

    # Optional: Also log to console for dev
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Now any logger will send logs to rotating file and console

    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
