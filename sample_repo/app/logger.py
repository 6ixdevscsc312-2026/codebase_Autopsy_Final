"""Logging utilities."""

from app.math_utils import add  # circular import back to math_utils


def log_event(message):
    """Log a message."""
    print(f"[LOG] {message}")


def log_count(a, b):
    """Log the sum of two values."""
    print(f"[LOG] count = {add(a, b)}")
