"""
Shelf item visualization.
Refactored: True HD Rendering (Item scaled via Transform, Pixmap full res).
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle, QGraphicsTextItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QBrush, QPen, QTransform, QPainter, QColor
from config import *


class ShelfItem(QGraphicsObject):
    clicked = pyqtSignal(int)
    
    _pixmaps = {}
    _images_loaded = False

    def __init__(self, x, y, index=0, size=SHELF_SIZE, show_label=True, 
                 angle=0, variant=1, mirrored=False):
        super().__init__()
        
        self.setPos(x, y)
        self.index = index
        self.target_size = size # Zielgröße in Map-Einheiten
        self.show_label = show_label
        
        self.angle = angle
        self.variant = variant if variant > 0 else 1
        self.mirrored = mirrored
        
        self._current_pixmap = None 
        
        self.setZValue(5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        
        self._load_images()
        self.set_visuals()
        self._create_label()
        
        self._update_transform()

    def _update_transform(self):
        # 1. Reset
        self.setTransform(QTransform())
        
        # 2. Skalierung berechnen (HD Rendering)
        if self._current_pixmap and self._current_pixmap.width() > 0:
            # Wir wollen, dass das riesige Bild auf 'target_size' Einheiten schrumpft
            scale_factor = self.target_size / self._current_pixmap.width()
            self.setScale(scale_factor)
        
        # 3. Rotation
        self.setRotation(self.angle)
        
        # 4. Spiegelung
        if self.mirrored:
            # Vorsicht: setScale überschreibt Transform. 
            # Besser: Wir nutzen QTransform chain
            base_trans = QTransform()
            base_trans.scale(-1 if self.mirrored else 1, 1)
            self.setTransform(base_trans, combine=True)

    @classmethod
    def _load_images(cls):
        if cls._images_loaded: return
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
        if not pix and 1 in self._pixmaps: pix = self._pixmaps[1]
        self._current_pixmap = pix
        
        # Origin muss immer 0,0 sein (wir zeichnen zentriert um 0,0)
        # Aber da wir setScale nutzen, ist 0,0 die Mitte des Items?
        # Nein, bei Pixmaps ist 0,0 meist Oben-Links.
        # Wir müssen boundingRect zentrieren.

    def boundingRect(self):
        # Das BoundingRect ist in Item-Koordinaten (also Originalauflösung!)
        if self._current_pixmap:
            w = self._current_pixmap.width()
            h = self._current_pixmap.height()
            return QRectF(-w/2, -h/2, w, h)
        return QRectF(-self.target_size/2, -self.target_size/2, self.target_size, self.target_size)

    def _create_label(self):
        self.label = QGraphicsTextItem(str(self.index + 1), self)
        font = QFont()
        # Font muss riesig sein, da das Item stark runterskaliert ist!
        # Wenn Scale = 0.05, muss Font = 200 sein um wie 10 auszusehen.
        scale_factor = 1.0
        if self._current_pixmap and self._current_pixmap.width() > 0:
            scale_factor = self._current_pixmap.width() / self.target_size
            
        font.setPixelSize(int(12 * scale_factor)) 
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(Qt.GlobalColor.white)

        br = self.label.boundingRect()
        self.label.setPos(-br.width() / 2, -br.height() / 2)
        
        # Label darf nicht gespiegelt werden
        if self.mirrored:
            tr = QTransform()
            tr.scale(-1, 1)
            self.label.setTransform(tr)
            
        self.label.setVisible(self.show_label)

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()

        if self._current_pixmap and not self._current_pixmap.isNull():
            # Zeichne das volle Bild in das volle Rect (HD)
            painter.drawPixmap(rect.toRect(), self._current_pixmap)
        else:
            painter.setBrush(QBrush(COLOR_SHELF))
            painter.setPen(QPen(Qt.GlobalColor.black, 10)) # Dicker Pen für HD
            painter.drawRect(rect)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # Pen Dicke an Scale anpassen
            pen_width = 4
            if self.scale() > 0: pen_width = 4 / self.scale()
            painter.setPen(QPen(COLOR_SELECTION, pen_width))
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)