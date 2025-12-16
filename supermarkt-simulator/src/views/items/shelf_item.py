"""
Shelf item visualization.
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush
from config import *


class ShelfItem(QGraphicsRectItem):
    """
    Visual representation of a shelf.
    """

    def __init__(self, x, y):
        """
        Initializes the shelf item.
        @param x: Center X coordinate.
        @param y: Center Y coordinate.
        """
        super().__init__(
            x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
        )
        self.setBrush(QBrush(COLOR_SHELF))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(5)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)

    def paint(self, painter, option, widget=None):
        """
        Paints the shelf.
        """
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 2))
        else:
            painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setBrush(self.brush())
        painter.drawRect(self.rect())
