"""
Shelf item visualization.
Refactored: Simplified - removed orientation.
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QStyle, QGraphicsTextItem
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

        # Draw ID Text
        self.label = QGraphicsTextItem(str(index + 1), self)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)

        # Center the label
        br = self.label.boundingRect()
        r = self.rect()
        self.label.setPos(
            r.center().x() - br.width() / 2, r.center().y() - br.height() / 2
        )

    def paint(self, painter, option, widget=None):
        """
        Paints the shelf selection border.
        """
        painter.setBrush(self.brush())
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 4))
        else:
            painter.setPen(self.pen())
        painter.drawRect(self.rect())
