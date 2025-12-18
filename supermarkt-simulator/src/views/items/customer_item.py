"""
Customer visualization module.
Refactored: Displays dynamic item count.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from config import *


class CustomerItem(QGraphicsEllipseItem):
    """
    Visual representation of a customer in the simulation scene.
    """

    def __init__(self, model):
        super().__init__(
            -CUSTOMER_SIZE / 2,
            -CUSTOMER_SIZE / 2,
            CUSTOMER_SIZE,
            CUSTOMER_SIZE,
        )
        self.model = model
        self.setBrush(QBrush(COLOR_CUSTOMER))
        self.setPen(QPen(Qt.GlobalColor.white))
        self.setZValue(20)
        self.setAcceptHoverEvents(True)
        self.sync_visuals()

    def sync_visuals(self):
        self.setPos(self.model.pos)
        self.update()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        # Draw Item Count (Accumulated)
        # Displays how many items the customer currently has
        count_str = str(self.model.item_count)

        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, count_str)

        # Draw Scan Progress
        if self.model.state == "SCANNING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SCAN_PROGRESS, 2))

            percent = 0.0
            if self.model.scan_duration_per_item > 0:
                percent = (
                    self.model.scan_time_elapsed
                    / self.model.scan_duration_per_item
                )

            # Clamp percentage
            percent = min(max(percent, 0.0), 1.0)

            angle = percent * 360 * 16
            rect = self.rect().adjusted(-2, -2, 2, 2)
            painter.drawArc(rect, 90 * 16, -int(angle))

    def hoverEnterEvent(self, event):
        self.setToolTip(
            f"Kunde\nItems: {self.model.item_count}\nStatus: {self.model.state}"
        )
        super().hoverEnterEvent(event)
