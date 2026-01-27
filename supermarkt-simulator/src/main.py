"""
Entry point for the application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from app_launcher import ApplicationLauncher


def main():
    """
    Main function to bootstrap the application.

    Initializes the QApplication and the ApplicationLauncher, then starts the event loop.
    """
    app = QApplication(sys.argv)
    launcher = ApplicationLauncher()
    launcher.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
