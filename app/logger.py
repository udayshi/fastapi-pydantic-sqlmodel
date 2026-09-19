"""Logging configuration."""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent format."""
    log = logging.getLogger(name)
    log.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log


logger = setup_logger(__name__)
