"""
Entry point for the application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from controllers.main_controller import MainController


def main():
    """
    Main function to bootstrap the application.

    Initializes the QApplication and the MainController, then starts the event loop.
    """
    app = QApplication(sys.argv)
    controller = MainController()
    controller.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
