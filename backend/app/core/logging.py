"""
Structured audit logging for the Smart City Complaint System.
Logs operations transparently without storing citizen PII in log streams.
"""

import logging
import sys


def setup_logger(name: str = "smart_city_backend") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()


def log_event(event_type: str, details: dict):
    """
    Log operational events with privacy preservation.
    Removes personal data like names or telephone numbers before logging.
    """
    safe_details = {k: v for k, v in details.items() if k not in {"citizen_name", "phone", "email"}}
    logger.info(f"EVENT={event_type} | {safe_details}")
