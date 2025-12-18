"""
Start Area visualization module.
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QFont
from config import COLOR_START_AREA, COLOR_TEXT_MAIN


class StartAreaItem(QGraphicsRectItem):
    """
    Visual representation of the start/spawn area.
    """

    def __init__(self, rect):
        """
        Initializes the start area item.
        @param rect: The QRectF defining the area.
        """
        super().__init__(rect)
        self.setBrush(QBrush(COLOR_START_AREA))

        # Dashed border to distinguish
        pen = QPen(COLOR_TEXT_MAIN)
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(2)
        self.setPen(pen)

        self.setZValue(1)  # Above floor, below objects

        # Label
        self.label = QGraphicsTextItem("START", self)
        font = QFont()
        font.setBold(True)
        font.setPixelSize(14)
        self.label.setFont(font)
        self.label.setDefaultTextColor(COLOR_TEXT_MAIN)

        # Center label
        r = self.rect()
        br = self.label.boundingRect()
        self.label.setPos(
            r.center().x() - br.width() / 2, r.center().y() - br.height() / 2
        )
