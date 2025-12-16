"""
Checkout item visualization.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainter, QColor
from config import *


class CheckoutItem(QGraphicsObject):
    """
    Visual representation of a checkout counter.
    Supports different types (Normal/SB) and orientations, including images and status lights.
    """

    _pixmap_normal_left = None
    _pixmap_normal_right = None
    _pixmap_sb_left = None
    _pixmap_sb_right = None

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
    ):
        """
        Initializes the checkout item.

        @param x: X position.
        @param y: Y position.
        @param c_type: Type of checkout ("Normal" or "SB").
        @param orientation: "Left" or "Right".
        @param is_open: Status of the checkout.
        @param show_light: Whether to draw the status light.
        @param data_id: ID of the checkout data object.
        @param light_offset: (x, y) tuple for light position relative to item.
        """
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_light = show_light
        self.data_id = data_id
        self.light_offset = light_offset
        self.setZValue(6)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        # Lazy loading of static pixmaps
        if CheckoutItem._pixmap_normal_left is None:
            p_n_l = IMAGE_DIR / "checkout_left.png"
            p_n_r = IMAGE_DIR / "checkout_right.png"
            p_s_l = IMAGE_DIR / "sb_checkout_left.png"
            p_s_r = IMAGE_DIR / "sb_checkout_right.png"
            if p_n_l.exists():
                CheckoutItem._pixmap_normal_left = QPixmap(str(p_n_l))
            if p_n_r.exists():
                CheckoutItem._pixmap_normal_right = QPixmap(str(p_n_r))
            if p_s_l.exists():
                CheckoutItem._pixmap_sb_left = QPixmap(str(p_s_l))
            if p_s_r.exists():
                CheckoutItem._pixmap_sb_right = QPixmap(str(p_s_r))

    def boundingRect(self):
        """
        Returns the bounding box of the checkout.
        @rtype: QRectF
        """
        return QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        """
        Paints the checkout image or fallback rectangle.
        """
        pixmap = None
        if self.c_type == "SB":
            pixmap = (
                CheckoutItem._pixmap_sb_left
                if self.orientation == "Left"
                else CheckoutItem._pixmap_sb_right
            )
        else:
            pixmap = (
                CheckoutItem._pixmap_normal_left
                if self.orientation == "Left"
                else CheckoutItem._pixmap_normal_right
            )

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(self.boundingRect().toRect(), pixmap)
        else:
            # Fallback drawing
            color = (
                QColor("#607D8B")
                if self.c_type == "Normal"
                else QColor("#455A64")
            )
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            painter.setPen(Qt.PenStyle.NoPen)
            if self.orientation == "Left":
                painter.drawRect(0, 0, 5, CHECKOUT_HEIGHT)
            else:
                painter.drawRect(CHECKOUT_WIDTH - 5, 0, 5, CHECKOUT_HEIGHT)

        # Selection highlight
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(-2, -2, CHECKOUT_WIDTH + 4, CHECKOUT_HEIGHT + 4)

        # Status Light
        if self.show_light:
            status_color = (
                Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            )
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawEllipse(
                self.light_offset[0], self.light_offset[1], 8, 8
            )
