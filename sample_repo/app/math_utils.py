"""Pure math utility functions. No side effects, no I/O."""

import json
from app.logger import log_event


def add(a, b):
    """Add two numbers."""
    return a + b


def compute_and_save_report(numbers, filepath):
    """Compute stats. (Drift: this actually writes files and logs -
    not what the module docstring promises.)"""
    total = sum(numbers)
    avg = total / len(numbers) if numbers else 0
    with open(filepath, "w") as f:
        json.dump({"total": total, "avg": avg}, f)
    log_event(f"Saved report to {filepath}")
    return total, avg
