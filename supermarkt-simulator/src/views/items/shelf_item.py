"""
Shelf item visualization.
Refactored: Supports dynamic sizing and label toggle.
"""

from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QStyle,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QFont, QBrush, QPen
from config import *
import random


class ShelfItem(QGraphicsPixmapItem):
    _pixmaps = []
    _images_loaded = False

    def __init__(self, x, y, index=0, size=SHELF_SIZE, show_label=True):
        super().__init__()
        self.setPos(x, y)
        self.index = index
        self.size = size
        self.show_label = show_label
        self.setZValue(5)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._load_images()
        self.set_visuals()
        self._create_label()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        for img_name in IMG_SHELVES:
            path = IMAGE_DIR / img_name
            if path.exists():
                cls._pixmaps.append(QPixmap(str(path)))
        cls._images_loaded = True

    def set_visuals(self):
        self.pixmap_data = (
            random.choice(ShelfItem._pixmaps) if ShelfItem._pixmaps else None
        )

        if self.pixmap_data:
            scaled = self.pixmap_data.scaled(
                int(self.size),
                int(self.size),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
            self.setOffset(-self.size / 2, -self.size / 2)

    def _create_label(self):
        self.label = QGraphicsTextItem(str(self.index + 1), self)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)

        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, -br.height() / 2)
        
        # Visibility control
        self.label.setVisible(self.show_label)

    def paint(self, painter, option, widget=None):
        if not self.pixmap() or self.pixmap().isNull():
            rect = QRectF(
                -self.size / 2, -self.size / 2, self.size, self.size
            )
            painter.setBrush(QBrush(COLOR_SHELF))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)

        super().paint(painter, option, widget)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SELECTION, 2))
            bbox = self.boundingRect()
            painter.drawRect(bbox)