"""
Shelf item visualization.
Refactored: Displays Index/ID and thicker selection border.
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush, QFont
from config import *


class ShelfItem(QGraphicsRectItem):
    """
    Visual representation of a shelf.
    """

    def __init__(self, x, y, index=0):
        """
        Initializes the shelf item.
        @param x: Center X coordinate.
        @param y: Center Y coordinate.
        @param index: The visible index/ID of the shelf.
        """
        super().__init__(
            x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
        )
        self.index = index
        self.setBrush(QBrush(COLOR_SHELF))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(5)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)

    def paint(self, painter, option, widget=None):
        """
        Paints the shelf with ID and selection state.
        """
        # Draw Base
        painter.setBrush(self.brush())

        # Thicker border on selection
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 4))  # Thicker border (4px)
        else:
            painter.setPen(QPen(Qt.GlobalColor.black, 1))

        painter.drawRect(self.rect())

        # Draw ID Text
        # Only if big enough or zoomed in, but shelf is small (20px).
        # We draw a very small number or just on hover?
        # Let's try drawing it simply on top.
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.white))
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.index + 1)
        )
