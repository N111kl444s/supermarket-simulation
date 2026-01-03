"""
Cashier item visualization.
Refactored: Dynamic sizing.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush
from config import *


class CashierItem(QGraphicsEllipseItem):
    """
    Visual representation of a cashier employee.
    """

    def __init__(self, x, y, skill, size=CASHIER_SIZE):
        # EllipseItem needs x, y, w, h. We offset by size/2 to center it.
        super().__init__(-size / 2, -size / 2, size, size)
        self.setPos(x, y)
        self.skill = skill
        self.size = size
        
        self.setBrush(QBrush(COLOR_CASHIER))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(25)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, e):
        self.setToolTip(f"Kassierer ({self.skill})")
        super().hoverEnterEvent(e)