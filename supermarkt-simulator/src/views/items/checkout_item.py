"""
Checkout item visualization.
Refactored: Displays ID and thicker selection border.
Fixed: mousePressEvent now propagates selection.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainter, QColor, QFont
from config import *


class CheckoutItem(QGraphicsObject):
    """
    Visual representation of a checkout counter.
    Supports different types (Normal/SB) and orientations, including images and status lights.
    """

    # Signal emittieren, wenn geklickt wird
    clicked = pyqtSignal(int)

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

        # Interaktivitaet
        self.setCursor(Qt.CursorShape.PointingHandCursor)
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
        """
        return QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        """
        Paints the checkout image, ID, and selection highlight.
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

        rect = self.boundingRect().toRect()

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(rect, pixmap)
        else:
            # Fallback drawing
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
                painter.drawRect(0, 0, 5, CHECKOUT_HEIGHT)
            else:
                painter.drawRect(CHECKOUT_WIDTH - 5, 0, 5, CHECKOUT_HEIGHT)

        # Selection highlight (Visible Border)
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 4))  # Thicker border
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(-2, -2, 2, 2))

        # Status Light
        if self.show_light:
            status_color = (
                Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            )
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawEllipse(
                int(self.light_offset[0]), int(self.light_offset[1]), 8, 8
            )

        # Draw ID Text (Top Center or Center)
        if self.data_id is not None:
            font = QFont()
            font.setPixelSize(14)
            font.setBold(True)
            painter.setFont(font)
            # Draw shadow for readability
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawText(
                rect.adjusted(1, 1, 1, 1),
                Qt.AlignmentFlag.AlignCenter,
                f"#{self.data_id}",
            )
            # Draw text
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, f"#{self.data_id}"
            )

    def mousePressEvent(self, event):
        """
        Handles mouse press events.
        """
        # ZUERST Standard-Selektion erlauben (wichtig fuer Editor-Modus)
        super().mousePressEvent(event)

        # DANN Signal senden (wichtig fuer Sim-Modus / Config)
        if event.button() == Qt.MouseButton.LeftButton:
            if self.data_id is not None:
                self.clicked.emit(self.data_id)
