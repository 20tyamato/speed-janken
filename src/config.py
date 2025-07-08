# src/config.py
import logging
import logging.config
import os


def init_logging_config():
    config_path = os.getenv("LOG_CONFIG_FILE_PATH")
    if not config_path or not os.path.exists(config_path):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(
            "The logging configuration file was not found, using basic configuration."
        )
        return

    try:
        defaults = {
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "LOG_FILE_PATH": os.getenv("LOG_FILE_PATH", "logs/sample.log"),
        }
        logging.config.fileConfig(
            config_path, disable_existing_loggers=False, defaults=defaults
        )
        logging.getLogger("httpx").setLevel(logging.WARNING)
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).exception(
            "Failed to load the logging configuration file, using basic configuration. Error: %s",
            e,
        )
