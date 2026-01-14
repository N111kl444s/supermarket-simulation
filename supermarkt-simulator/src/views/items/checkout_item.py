"""
Checkout item visualization.
Refactored: Right-Click Edit & Thin Selection Frame.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainter, QColor, QFont, QTransform
from config import *

class CheckoutItem(QGraphicsObject):
    clicked = pyqtSignal(int)
    
    _pixmap_normal = None
    _pixmap_sb = None
    _images_loaded = False

    def __init__(self, x, y, c_type="Normal", orientation="Right", is_open=True, show_light=True, data_id=None, light_offset=(0, 0), width=CHECKOUT_WIDTH, height=CHECKOUT_HEIGHT, angle=0, show_id=True):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_light = show_light
        self.data_id = data_id
        self.show_id = show_id
        
        self.width = width
        self.height = height
        self.angle = angle
        
        self.setZValue(6)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        
        # FIX: Rechtsklick erlauben
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)
        
        self.setTransformOriginPoint(self.width / 2, self.height / 2)
        self.setRotation(self.angle)
        
        if self.orientation == "Left":
            trans = QTransform()
            trans.scale(-1, 1) 
            self.setTransform(trans, combine=True)

        self.light_offset = (light_offset if light_offset != (0, 0) else (self.width / 2, 10))
        self._load_images()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded: return
        p_n = IMAGE_DIR / "kasse.png"
        p_s = IMAGE_DIR / "sb.png"
        if p_n.exists(): cls._pixmap_normal = QPixmap(str(p_n))
        if p_s.exists(): cls._pixmap_sb = QPixmap(str(p_s))
        cls._images_loaded = True

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = self._pixmap_sb if self.c_type == "SB" else self._pixmap_normal
        rect = self.boundingRect().toRect()

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(rect, pixmap)
        else:
            color = QColor("#607D8B") if self.c_type == "Normal" else QColor("#455A64")
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)
            painter.setPen(Qt.GlobalColor.white)
            painter.save()
            if self.transform().m11() < 0:
                 painter.scale(-1, 1); painter.translate(-self.width, 0)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.c_type)
            painter.restore()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            # FIX: Dünnerer Rahmen (1.5)
            painter.setPen(QPen(COLOR_SELECTION, 1.5))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

        if self.show_light:
            status_color = Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            lx, ly = self.light_offset
            if isinstance(lx, (list, tuple)): lx, ly = lx[0], lx[1]
            painter.drawEllipse(int(lx), int(ly), 8, 8)

        if self.data_id is not None and self.show_id:
            painter.save()
            if self.orientation == "Left":
                painter.translate(self.width / 2, self.height / 2)
                painter.scale(-1, 1)
                painter.translate(-self.width / 2, -self.height / 2)
            font = QFont(); font.setPixelSize(12); font.setBold(True); painter.setFont(font)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(rect.adjusted(2, 2, 2, 2), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"#{self.data_id}")
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(rect.adjusted(1, 1, 1, 1), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"#{self.data_id}")
            painter.restore()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.accept()
        
        # FIX: Rechtsklick
        if event.button() == Qt.MouseButton.RightButton:
            if self.data_id is not None:
                self.clicked.emit(self.data_id)