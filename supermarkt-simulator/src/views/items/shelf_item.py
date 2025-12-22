"""
Shelf item visualization.
Refactored: Uses images from config or fallback rectangle.
Fixed: Positioning logic (setPos) added.
"""

from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QStyle,
    QGraphicsRectItem,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QFont, QColor, QBrush, QPen
from config import *
import random


class ShelfItem(QGraphicsPixmapItem):
    """
    Visual representation of a shelf using images.
    """

    _pixmaps = []
    _images_loaded = False

    def __init__(self, x, y, index=0):
        super().__init__()

        # WICHTIG: Position setzen!
        self.setPos(x, y)

        self.index = index
        self.setZValue(5)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._load_images()
        self.set_visuals()
        self._create_label()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        # Lade Bilder basierend auf der dynamischen Liste in Config
        for img_name in IMG_SHELVES:
            path = IMAGE_DIR / img_name
            if path.exists():
                cls._pixmaps.append(QPixmap(str(path)))
            else:
                print(f"Fehler: Regal-Bild nicht gefunden: {path}")
        cls._images_loaded = True

    def set_visuals(self):
        # Wähle zufälliges Bild oder Fallback
        self.pixmap_data = (
            random.choice(ShelfItem._pixmaps) if ShelfItem._pixmaps else None
        )

        if self.pixmap_data:
            scaled = self.pixmap_data.scaled(
                SHELF_SIZE,
                SHELF_SIZE,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(scaled)
            self.setOffset(-SHELF_SIZE / 2, -SHELF_SIZE / 2)
        else:
            # Fallback: Wenn keine Bilder da sind, wird im paint() gezeichnet
            pass

    def _create_label(self):
        self.label = QGraphicsTextItem(str(self.index + 1), self)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)

        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, -br.height() / 2)

    def paint(self, painter, option, widget=None):
        # Falls kein Bild geladen wurde, zeichne ein graues Rechteck als Fallback
        if not self.pixmap() or self.pixmap().isNull():
            rect = QRectF(
                -SHELF_SIZE / 2, -SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
            )
            painter.setBrush(QBrush(COLOR_SHELF))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)

        super().paint(painter, option, widget)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SELECTION, 2))
            # Rahmen um das Bild (oder Fallback Rect)
            bbox = self.boundingRect()
            painter.drawRect(bbox)
