# src/common.py
import logging

import dotenv

from config import init_logging_config

dotenv.load_dotenv()
init_logging_config()

logger = logging.getLogger(__name__)
