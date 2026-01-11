"""
Checkout item visualization.
Refactored: Supports Rotation (Angle) and ID toggle.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainter, QColor, QFont
from config import *


class CheckoutItem(QGraphicsObject):
    clicked = pyqtSignal(int)
    _pixmap_normal_left = None
    _pixmap_normal_right = None
    _pixmap_sb_left = None
    _pixmap_sb_right = None
    _images_loaded = False

    def __init__(
        self,
        x,
        y,
        c_type="Normal",
        orientation="Right",
        is_open=True,
        show_light=True,
        data_id=None,
        light_offset=(0, 0),
        width=CHECKOUT_WIDTH,
        height=CHECKOUT_HEIGHT,
        angle=0,
        show_id=True # NEU: Toggle für ID
    ):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_light = show_light
        self.data_id = data_id
        self.show_id = show_id # Speichern
        
        self.width = width
        self.height = height
        self.angle = angle
        
        self.setTransformOriginPoint(self.width / 2, self.height / 2)
        self.setRotation(self.angle)
        
        self.light_offset = (
            light_offset
            if light_offset != (0, 0)
            else (self.width / 2, 10)
        )
        self.setZValue(6)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        self._load_images()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        p_n_l = IMAGE_DIR / "kasse_l.png"
        p_n_r = IMAGE_DIR / "kasse_r.png"
        p_s_l = IMAGE_DIR / "sb_l.png"
        p_s_r = IMAGE_DIR / "sb_r.png"

        if p_n_l.exists():
            cls._pixmap_normal_left = QPixmap(str(p_n_l))
        if p_n_r.exists():
            cls._pixmap_normal_right = QPixmap(str(p_n_r))
        if p_s_l.exists():
            cls._pixmap_sb_left = QPixmap(str(p_s_l))
        if p_s_r.exists():
            cls._pixmap_sb_right = QPixmap(str(p_s_r))

        cls._images_loaded = True

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = None
        if self.c_type == "SB":
            pixmap = (
                self._pixmap_sb_left
                if self.orientation == "Left"
                else self._pixmap_sb_right
            )
        else:
            pixmap = (
                self._pixmap_normal_left
                if self.orientation == "Left"
                else self._pixmap_normal_right
            )

        rect = self.boundingRect().toRect()

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                int(self.width),
                int(self.height),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(0, 0, scaled)
        else:
            color = (
                QColor("#607D8B")
                if self.c_type == "Normal"
                else QColor("#455A64")
            )
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)

            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            painter.setPen(Qt.PenStyle.NoPen)
            if self.orientation == "Left":
                painter.drawRect(0, 0, 5, int(self.height))
            else:
                painter.drawRect(int(self.width) - 5, 0, 5, int(self.height))

            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.c_type)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

        if self.show_light:
            status_color = (
                Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            )
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            lx, ly = self.light_offset
            if isinstance(lx, (list, tuple)):
                lx, ly = lx[0], lx[1]
            painter.drawEllipse(int(lx), int(ly), 8, 8)

        # FIX: Nur zeichnen, wenn aktiviert
        if self.data_id is not None and self.show_id:
            font = QFont()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            
            painter.setPen(QPen(Qt.GlobalColor.black))
            text_rect = rect.adjusted(2, 2, 2, 2)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                f"#{self.data_id}",
            )
            painter.setPen(QPen(Qt.GlobalColor.white))
            text_rect = rect.adjusted(1, 1, 1, 1)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                f"#{self.data_id}",
            )

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if self.data_id is not None:
                self.clicked.emit(self.data_id)