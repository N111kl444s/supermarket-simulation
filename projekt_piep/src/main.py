# src/main.py

import sys
from PyQt6.QtWidgets import QApplication
from controller.main_controller import MainController


def main():
    """Application Entry Point."""
    app = QApplication(sys.argv)

    # MVC Initialization
    # Controller creates Model and View internally
    controller = MainController()
    controller.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
