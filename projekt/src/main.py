import sys
from PyQt6.QtWidgets import QApplication
from mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)

    # Controller/Window Instanziierung
    window = MainWindow()

    # Hier war vermutlich dein Fehler ("controller.show()" existierte nicht)
    # Jetzt rufen wir .show() direkt auf dem Window auf.
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
