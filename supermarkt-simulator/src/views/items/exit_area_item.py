"""
Visual representation of the Exit Area.
"""

from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt
from config import COLOR_EXIT_AREA, COLOR_RED


class ExitAreaItem(QGraphicsRectItem):
    def __init__(self, rect):
        super().__init__(rect)
        self.setBrush(QBrush(COLOR_EXIT_AREA))
        self.setPen(QPen(COLOR_RED, 2, Qt.PenStyle.DashLine))
        self.setZValue(1)
        
        # Optional: Label
        # self.setToolTip("Ausgangsfläche (Despawn)")