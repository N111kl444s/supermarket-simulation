"""
Shelf item visualization.
Updated: Inherits QObject to support 'clicked' signal.
"""

from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QStyle,
)
from PyQt6.QtCore import Qt, QRectF, QObject, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QBrush, QPen, QTransform
from config import *


class ShelfItem(QObject, QGraphicsPixmapItem):
    # Signal senden, wenn geklickt (Index des Regals)
    clicked = pyqtSignal(int)
    
    _pixmaps = {}
    _images_loaded = False

    def __init__(self, x, y, index=0, size=SHELF_SIZE, show_label=True, 
                 angle=0, variant=1, mirrored=False):
        # QObject Init
        QObject.__init__(self)
        # GraphicsItem Init
        QGraphicsPixmapItem.__init__(self)
        
        self.setPos(x, y)
        self.index = index
        self.size = size
        self.show_label = show_label
        
        self.angle = angle
        self.variant = variant if variant > 0 else 1
        self.mirrored = mirrored
        
        self.setZValue(5)
        # Hand Cursor signalisiert Klickbarkeit
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        self.setTransformOriginPoint(0, 0)
        self.setRotation(self.angle)
        
        if self.mirrored:
            tr = QTransform()
            tr.scale(-1, 1)
            self.setTransform(tr)

        self._load_images()
        self.set_visuals()
        self._create_label()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        
        for i in range(1, 6):
            path = IMAGE_DIR / f"regal{i}.png"
            if path.exists():
                cls._pixmaps[i] = QPixmap(str(path))
            else:
                fallback = IMAGE_DIR / "regal.png"
                if fallback.exists():
                    cls._pixmaps[i] = QPixmap(str(fallback))
                    
        cls._images_loaded = True

    def set_visuals(self):
        pix = self._pixmaps.get(self.variant)
        if not pix and 1 in self._pixmaps:
            pix = self._pixmaps[1]

        if pix:
            scaled = pix.scaled(
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
        
        if self.mirrored:
            tr = QTransform()
            tr.scale(-1, 1)
            self.label.setTransform(tr)
            
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

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)