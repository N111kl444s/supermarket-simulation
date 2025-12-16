"""
Cashier item visualization.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush
from config import *


class CashierItem(QGraphicsEllipseItem):
    """
    Visual representation of a cashier employee.
    """

    def __init__(self, x, y, skill):
        """
        Initializes the cashier item.
        @param x: X position.
        @param y: Y position.
        @param skill: Skill level string.
        """
        super().__init__(0, 0, CASHIER_SIZE, CASHIER_SIZE)
        self.setPos(x, y)
        self.setBrush(QBrush(COLOR_CASHIER))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(25)
        self.skill = skill
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, e):
        """
        Show tooltip on hover.
        """
        self.setToolTip(f"Kassierer ({self.skill})")
        super().hoverEnterEvent(e)
