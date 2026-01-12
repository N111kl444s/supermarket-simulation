"""
Shelf item visualization.
Refactored: Uses QGraphicsObject (safe) instead of Mixin (unsafe) to prevent Segfaults.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle, QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPixmap,
    QFont,
    QBrush,
    QPen,
    QTransform,
    QPainter,
    QColor,
)
from config import *


class ShelfItem(QGraphicsObject):
    # Signale funktionieren jetzt nativ, da QGraphicsObject von QObject erbt
    clicked = pyqtSignal(int)

    _pixmaps = {}
    _images_loaded = False

    def __init__(
        self,
        x,
        y,
        index=0,
        size=SHELF_SIZE,
        show_label=True,
        angle=0,
        variant=1,
        mirrored=False,
    ):
        super().__init__()

        self.setPos(x, y)
        self.index = index
        self.size = size
        self.show_label = show_label

        self.angle = angle
        self.variant = variant if variant > 0 else 1
        self.mirrored = mirrored

        self._current_pixmap = None  # Speichert das aktuelle Bild für paint()

        self.setZValue(5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        # Origin in die Mitte für Rotation
        self.setTransformOriginPoint(0, 0)
        self.setRotation(self.angle)

        if self.mirrored:
            tr = QTransform()
            tr.scale(-1, 1)
            self.setTransform(tr)

        self._load_images()
        self.set_visuals()

        # Label muss Kind-Objekt sein, aber wir zeichnen es lieber im paint()
        # oder als Sub-Item. Hier als Sub-Item, da einfacher zu handhaben.
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
        # Bild auswählen
        pix = self._pixmaps.get(self.variant)
        if not pix and 1 in self._pixmaps:
            pix = self._pixmaps[1]

        if pix:
            # Wir skalieren das Bild vor und speichern es
            self._current_pixmap = pix.scaled(
                int(self.size),
                int(self.size),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    def boundingRect(self):
        # Definiert den klickbaren Bereich (zentriert um 0,0)
        return QRectF(-self.size / 2, -self.size / 2, self.size, self.size)

    def _create_label(self):
        # Label initialisieren
        self.label = QGraphicsTextItem(str(self.index + 1), self)
        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)

        # Zentrieren
        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, -br.height() / 2)

        # Ent-Spiegeln falls nötig
        if self.mirrored:
            tr = QTransform()
            tr.scale(-1, 1)
            self.label.setTransform(tr)

        self.label.setVisible(self.show_label)

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()

        # Bild zeichnen
        if self._current_pixmap and not self._current_pixmap.isNull():
            # Zeichne Pixmap zentriert auf das Rect
            painter.drawPixmap(
                int(rect.x()), int(rect.y()), self._current_pixmap
            )
        else:
            # Fallback (Rechteck)
            painter.setBrush(QBrush(COLOR_SHELF))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)

        # Auswahl-Rahmen
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(COLOR_SELECTION, 2))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
