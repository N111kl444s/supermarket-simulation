"""
Custom widget module.
"""

from PyQt6.QtWidgets import QGroupBox
from PyQt6.QtCore import pyqtSignal, Qt


class ClickableGroupBox(QGroupBox):
    """
    A QGroupBox that emits a signal when clicked.

    @ivar clicked: Signal emitted on left mouse click.
    @type clicked: pyqtSignal
    """

    clicked = pyqtSignal()

    def __init__(self, title, parent=None):
        """
        Initializes the group box.

        @param title: Title of the group box.
        @type title: str
        @param parent: Parent widget.
        @type parent: QWidget
        """
        super().__init__(title, parent)

    def mousePressEvent(self, e):
        """
        Handles mouse press events.

        @param e: Mouse event.
        @type e: QMouseEvent
        """
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)
