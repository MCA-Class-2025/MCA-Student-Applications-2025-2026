"""
utils/logging.py — Centralised logging configuration using loguru.
"""

import sys
from loguru import logger


def setup_logger(level: str = "INFO") -> None:
    """Configure loguru for the application."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )
    logger.add(
        "medicine_safety.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} — {message}",
    )


# Expose a ready-to-use logger
setup_logger()

__all__ = ["logger"]
