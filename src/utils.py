# src/utils.py
import os

import yaml

from src.common import logger


def get_env_var(var_name: str) -> str:
    env_var = os.environ.get(var_name)
    if not env_var:
        err_msg = f"{var_name} is not set in the environment variables."
        logger.error(err_msg)
        raise EnvironmentError(err_msg)
    return env_var


def load_yaml_config(config_path: str = "config.yaml") -> dict:
    if not os.path.exists(config_path):
        err_msg = f"Configuration file '{config_path}' not found."
        logger.error(err_msg)
        raise FileNotFoundError(err_msg)

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config
