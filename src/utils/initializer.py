import logging
import os
import pathlib
import sys

from src.config.config import Config
from src.utils.logger_config import setup_logger


def initialize():
    """
    The main setup function for the APP. Sets up directories and loggers.
    """
    ensure_directories_present()
    setup_logger()


def ensure_directories_present() -> None:
    """
    Ensures required directories exist and are writable.
    If any directory is not writable, logs error and exits the app.
    """
    dirs = ["models", "sample_data", "chroma_store", "logs"]
    logger = logging.getLogger(__name__)
    config = Config()

    for dir_name in dirs:
        full_path = pathlib.Path(config.ROOT_DIR) / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if not os.access(full_path, os.W_OK):
                logger.error(
                    "Directory '%s' is not writable by the app. "
                    "Please delete the directories: models, chroma_store, logs, sample_data "
                    "and run the makefile again.",
                    full_path,
                )
                sys.exit(1)
            else:
                logger.info("Directory ready and writable: %s", full_path)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to create or access directory '%s': %s", full_path, e)
            sys.exit(1)
