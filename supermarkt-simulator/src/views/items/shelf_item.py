"""
Shelf item visualization.
Refactored: Implemented shape() for precise hit detection.
"""

from PyQt6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPixmap,
    QFont,
    QBrush,
    QPen,
    QTransform,
    QPainter,
    QColor,
    QPainterPath,
)
from config import *


class ShelfItem(QGraphicsObject):
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
        self.target_size = size
        self.show_label = show_label
        self.angle = angle
        self.variant = variant if variant > 0 else 1
        self.mirrored = mirrored
        self._current_pixmap = None

        self.setZValue(5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
        )

        self._load_images()
        self.set_visuals()
        self._create_label()
        self._update_transform()

    def _update_transform(self):
        self.setTransform(QTransform())
        if self._current_pixmap and self._current_pixmap.width() > 0:
            scale_factor = self.target_size / self._current_pixmap.width()
            self.setScale(scale_factor)
        self.setRotation(self.angle)
        if self.mirrored:
            base_trans = QTransform()
            base_trans.scale(-1, 1)
            self.setTransform(base_trans, combine=True)

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        for i in range(1, 6):
            path = IMAGE_DIR / f"shelf{i}.png"
            if path.exists():
                cls._pixmaps[i] = QPixmap(str(path))
            else:
                fallback = IMAGE_DIR / "shelf.png"
                if fallback.exists():
                    cls._pixmaps[i] = QPixmap(str(fallback))
        cls._images_loaded = True

    def set_visuals(self):
        pix = self._pixmaps.get(self.variant)
        if not pix and 1 in self._pixmaps:
            pix = self._pixmaps[1]
        self._current_pixmap = pix

    def boundingRect(self):
        if self._current_pixmap:
            w = self._current_pixmap.width()
            h = self._current_pixmap.height()
            return QRectF(-w / 2, -h / 2, w, h)
        return QRectF(
            -self.target_size / 2,
            -self.target_size / 2,
            self.target_size,
            self.target_size,
        )

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def _create_label(self):
        self.label = QGraphicsTextItem(str(self.index + 1), self)
        font = QFont()
        scale_factor = 1.0
        if self._current_pixmap and self._current_pixmap.width() > 0:
            scale_factor = self._current_pixmap.width() / self.target_size
        font.setPixelSize(int(12 * scale_factor))
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

    def set_selectable(self, selectable: bool):
        """Enable/disable selection capability."""
        self.setFlag(
            QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, selectable
        )

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()
        if self._current_pixmap and not self._current_pixmap.isNull():
            painter.drawPixmap(rect.toRect(), self._current_pixmap)
        else:
            painter.setBrush(QBrush(COLOR_SHELF))
            painter.setPen(QPen(Qt.GlobalColor.black, 10))
            painter.drawRect(rect)

        # Draw red selection rectangle only in editor mode when selected
        if option.state & QStyle.StateFlag.State_Selected:
            scene = self.scene()
            if scene is not None and scene.is_editor_mode:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                pen_width = 1.0
                if self.scale() > 0:
                    pen_width = 1.0 / self.scale()
                painter.setPen(QPen(COLOR_SELECTION, pen_width))
                painter.drawRect(rect)

    def mousePressEvent(self, event):
        event.accept()
        if (
            event.button() == Qt.MouseButton.LeftButton
            or event.button() == Qt.MouseButton.RightButton
        ):
            self.clicked.emit(self.index)
