"""
Utility functions for TaskFlow API.
Logging setup, configuration validation, and helper functions.
"""

import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application logging with structured format."""
    logger = logging.getLogger('taskflow')
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def validate_config(config: dict[str, Any]) -> None:
    """Validate that required configuration values are present and valid."""
    required_keys = ['SECRET_KEY', 'DATABASE_URL']
    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required config: {key}")

    if config.get('SECRET_KEY') == 'dev-secret-key':
        logging.getLogger('taskflow').warning(
            "Using default SECRET_KEY — set SECRET_KEY env var in production"
        )


def paginate(items: list, page: int = 1, per_page: int = 20) -> dict:
    """Paginate a list of items."""
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': (total + per_page - 1) // per_page,
        'has_next': end < total,
        'has_prev': page > 1,
    }


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Basic input sanitization."""
    if not isinstance(text, str):
        return str(text)
    return text.strip()[:max_length]
