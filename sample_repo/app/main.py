"""Application entry point."""

from app.math_utils import compute_and_save_report


def run():
    """Run the app."""
    compute_and_save_report([1, 2, 3, 4], "/tmp/report.json")


if __name__ == "__main__":
    run()
