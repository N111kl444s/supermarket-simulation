"""
Waiting area visualization.
"""

from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush
from config import *


class WaitingAreaItem(QGraphicsRectItem):
    """
    Visual representation of the waiting area zone.
    """

    def __init__(self, rect):
        """
        Initializes the waiting area item.
        @param rect: The QRectF defining the area.
        """
        super().__init__(rect)
        self.setBrush(QBrush(COLOR_WAITING_AREA))
        self.setPen(QPen(COLOR_GREEN, 2, Qt.PenStyle.DashLine))
        self.setZValue(2)
