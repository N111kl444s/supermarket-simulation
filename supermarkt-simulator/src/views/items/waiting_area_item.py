"""
Waiting area visualization.
"""

from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush
from config import COLOR_WAITING_AREA, COLOR_SUCCESS


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
        # Updated to use COLOR_SUCCESS instead of COLOR_GREEN
        self.setPen(QPen(COLOR_SUCCESS, 2, Qt.PenStyle.DashLine))
        self.setZValue(2)
