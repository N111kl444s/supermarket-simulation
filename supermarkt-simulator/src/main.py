"""
Entry point for the application.
"""

import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from controllers.main_controller import MainController


def main():
    """
    Main function to bootstrap the application.
    """
    try:
        app = QApplication(sys.argv)
        controller = MainController()
        controller.show()
        sys.exit(app.exec())
    except Exception:
        # Fängt jeden Fehler ab und zeigt ihn an, bevor das Programm stirbt
        error_msg = traceback.format_exc()
        print(error_msg) # Ins Terminal drucken
        # Versuch, eine Message Box zu zeigen (falls Qt schon läuft)
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Ein kritischer Fehler ist aufgetreten")
            msg.setInformativeText(error_msg)
            msg.setWindowTitle("Absturz")
            msg.exec()
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()