"""
Checkout item visualization.
Refactored: Renamed light parameters to screen.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QPixmap,
    QPainter,
    QColor,
    QFont,
    QTransform,
    QPainterPath,
)
from config import *


class CheckoutItem(QGraphicsObject):
    clicked = pyqtSignal(int)
    _pixmap_normal = None
    _pixmap_sb = None
    _images_loaded = False

    def __init__(
        self,
        x,
        y,
        c_type="Normal",
        orientation="Right",
        is_open=True,
        show_screen=True,
        data_id=None,
        screen_offset=(0, 0),
        width=CHECKOUT_WIDTH,
        height=CHECKOUT_HEIGHT,
        angle=0,
        show_id=True,
    ):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_screen = show_screen
        self.data_id = data_id
        self.show_id = show_id

        self.width = width
        self.height = height
        self.angle = angle

        self.setZValue(6)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton
        )

        self.setTransformOriginPoint(self.width / 2, self.height / 2)
        self.setRotation(self.angle)

        if self.orientation == "Left":
            trans = QTransform()
            trans.scale(-1, 1)
            self.setTransform(trans, combine=True)

        self._load_images()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        p_n = IMAGE_DIR / "cash_register.png"
        p_s = IMAGE_DIR / "self_service.png"
        if p_n.exists():
            cls._pixmap_normal = QPixmap(str(p_n))
        if p_s.exists():
            cls._pixmap_sb = QPixmap(str(p_s))
        cls._images_loaded = True

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def set_selectable(self, selectable: bool):
        """Enable/disable selection capability."""
        self.setFlag(
            QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, selectable
        )

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = (
            self._pixmap_sb if self.c_type == "SB" else self._pixmap_normal
        )
        rect = self.boundingRect().toRect()

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(rect, pixmap)
        else:
            color = (
                QColor("#607D8B")
                if self.c_type == "Normal"
                else QColor("#455A64")
            )
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)
            painter.setPen(Qt.GlobalColor.white)
            painter.save()
            if self.transform().m11() < 0:
                painter.scale(-1, 1)
                painter.translate(-self.width, 0)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.c_type)
            painter.restore()

        # Draw red selection rectangle only in editor mode when selected
        if option.state & QStyle.StateFlag.State_Selected:
            scene = self.scene()
            if scene is not None and scene.is_editor_mode:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(COLOR_SELECTION, 1.5))
                painter.drawRect(rect.adjusted(1, 1, -1, -1))

        # SCREEN IS DRAWN EXTERNALLY IN VISUAL CONTROLLER

        if self.data_id is not None and self.show_id:
            painter.save()
            if self.orientation == "Left":
                painter.translate(self.width / 2, self.height / 2)
                painter.scale(-1, 1)
                painter.translate(-self.width / 2, -self.height / 2)
            font = QFont()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(
                rect.adjusted(2, 2, 2, 2),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                f"#{self.data_id}",
            )
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(
                rect.adjusted(1, 1, 1, 1),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                f"#{self.data_id}",
            )
            painter.restore()

    def mousePressEvent(self, event):
        event.accept()
        if (
            event.button() == Qt.MouseButton.LeftButton
            or event.button() == Qt.MouseButton.RightButton
        ):
            if self.data_id is not None:
                self.clicked.emit(self.data_id)
