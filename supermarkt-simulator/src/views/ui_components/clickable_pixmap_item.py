"""
Custom graphics item module.
"""

from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import pyqtSignal, Qt, QRectF


class ClickablePixmapItem(QGraphicsObject):
    """
    A QGraphicsObject displaying a pixmap that responds to clicks.

    @ivar clicked: Signal emitted on left mouse click.
    @type clicked: pyqtSignal
    """

    clicked = pyqtSignal()

    def __init__(self, pixmap, parent=None):
        """
        Initializes the item.

        @param pixmap: The image to display.
        @type pixmap: QPixmap
        @param parent: Parent item.
        @type parent: QGraphicsItem
        """
        super().__init__(parent)
        self.pixmap = pixmap

    def boundingRect(self):
        """
        Defines the bounding rectangle of the item.

        @return: The bounding rectangle.
        @rtype: QRectF
        """
        return QRectF(self.pixmap.rect())

    def paint(self, painter, option, widget=None):
        """
        Paints the item.

        @param painter: The painter object.
        @type painter: QPainter
        @param option: Style options.
        @param widget: The widget being painted on.
        """
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, e):
        """
        Handles mouse press events.

        @param e: Mouse event.
        @type e: QGraphicsSceneMouseEvent
        """
        print("Test")
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            e.accept()
        else:
            super().mousePressEvent(e)
