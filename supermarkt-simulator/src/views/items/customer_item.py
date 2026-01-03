"""
Customer visualization module.
Refactored: Supports dynamic sizing via init parameter.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPixmap
from config import *
import random


class CustomerItem(QGraphicsPixmapItem):
    _pixmaps_normal = []
    _pixmaps_disabled = []
    _images_loaded = False

    def __init__(self, model, size=CUSTOMER_SIZE):
        super().__init__()
        self.model = model
        self.size = size  # Dynamic size
        self.setZValue(20)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)

        self._ensure_images_loaded()
        self._assign_image()
        self.sync_visuals()

    @classmethod
    def _ensure_images_loaded(cls):
        if cls._images_loaded:
            return

        for img_name in IMG_CUSTOMERS_NORMAL:
            path = IMAGE_DIR / img_name
            if path.exists():
                cls._pixmaps_normal.append(QPixmap(str(path)))

        for img_name in IMG_CUSTOMERS_DISABLED:
            path = IMAGE_DIR / img_name
            if path.exists():
                cls._pixmaps_disabled.append(QPixmap(str(path)))

        cls._images_loaded = True

    def _assign_image(self):
        pool = []
        if self.model.is_disabled:
            pool = CustomerItem._pixmaps_disabled
            if not pool:
                pool = CustomerItem._pixmaps_normal
        else:
            pool = CustomerItem._pixmaps_normal

        if pool:
            pix = random.choice(pool)
            scaled = pix.scaled(
                int(self.size),
                int(self.size),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
            self.setOffset(-self.size / 2, -self.size / 2)

    def sync_visuals(self):
        self.setPos(self.model.pos)
        self.update()

    def boundingRect(self):
        base_rect = super().boundingRect()
        return base_rect.adjusted(-5, -18, 5, 5)

    def paint(self, painter, option, widget=None):
        if not self.pixmap() or self.pixmap().isNull():
            color = COLOR_ACCENT if self.model.is_disabled else COLOR_CUSTOMER
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawEllipse(
                int(-self.size / 2),
                int(-self.size / 2),
                int(self.size),
                int(self.size),
            )

        super().paint(painter, option, widget)

        # Item Count Badge
        count_str = str(self.model.item_count)
        painter.setBrush(QBrush(QColor(0, 0, 0, 160)))
        painter.setPen(Qt.PenStyle.NoPen)

        # Position badge slightly higher
        badge_rect = QRectF(-self.size / 2, -self.size / 2 - 14, 20, 14)
        painter.drawRoundedRect(badge_rect, 6, 6)

        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, count_str)

        # Scan Progress Ring
        if self.model.state == "SCANNING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SCAN_PROGRESS, 3))
            percent = 0.0
            if self.model.scan_duration_per_item > 0:
                percent = (
                    self.model.scan_time_elapsed
                    / self.model.scan_duration_per_item
                )
            percent = min(max(percent, 0.0), 1.0)
            angle = percent * 360 * 16

            rect = super().boundingRect().adjusted(-2, -2, 2, 2)
            painter.drawArc(rect.toRect(), 90 * 16, -int(angle))

    def hoverEnterEvent(self, event):
        status = "Behinderung" if self.model.is_disabled else "Normal"
        self.setToolTip(
            f"Typ: {status}\nItems: {self.model.item_count}\nStatus: {self.model.state}"
        )
        super().hoverEnterEvent(event)