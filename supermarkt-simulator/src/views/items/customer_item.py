"""
Customer visualization module.
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QFont
from config import *


class CustomerItem(QGraphicsEllipseItem):
    """
    Visual representation of a customer in the simulation scene.

    Observes a CustomerModel and updates its position and appearance accordingly.
    """

    def __init__(self, model):
        """
        Initializes the customer item.

        @param model: The data model backing this visual item.
        @type model: CustomerModel
        """
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
        """
        Synchronizes the visual position with the model's position.
        """
        self.setPos(self.model.pos)
        self.update()

    def paint(self, painter, option, widget=None):
        """
        Paints the customer, inventory count, and scan progress.

        @param painter: Painter object.
        @type painter: QPainter
        @param option: Style options.
        @param widget: Widget.
        """
        super().paint(painter, option, widget)

        # Draw Inventory
        remaining = max(0, self.model.inventory - self.model.items_scanned)
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter, str(remaining)
        )

        # Draw Scan Progress
        if self.model.state == "SCANNING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SCAN_PROGRESS, 2))
            angle = (
                (self.model.scan_progress_ticks / self.model.scan_ticks_total)
                * 360
                * 16
            )
            rect = self.rect().adjusted(-2, -2, 2, 2)
            painter.drawArc(rect, 90 * 16, -int(angle))

    def hoverEnterEvent(self, event):
        """
        Handles mouse hover events to show tooltips.

        @param event: Hover event.
        @type event: QGraphicsSceneHoverEvent
        """
        self.setToolTip(
            f"Kunde\nItems: {self.model.inventory}\nState: {self.model.state}"
        )
        super().hoverEnterEvent(event)
