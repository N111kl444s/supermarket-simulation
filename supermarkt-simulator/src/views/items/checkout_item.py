"""
Checkout item visualization.
Refactored: Robust image loading with fallbacks and status lights.
"""

from PyQt6.QtWidgets import QGraphicsObject, QStyle
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainter, QColor, QFont
from config import *


class CheckoutItem(QGraphicsObject):
    """
    Visual representation of a checkout counter.
    Uses specific images for orientation and type.
    """

    clicked = pyqtSignal(int)

    # Static Cache
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
    ):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.show_light = show_light
        self.data_id = data_id
        # Use default light offsets if 0,0 passed
        self.light_offset = (
            light_offset
            if light_offset != (0, 0)
            else (CHECKOUT_WIDTH / 2, 10)
        )
        self.setZValue(6)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable, True)

        self._load_images()

    @classmethod
    def _load_images(cls):
        """Loads images once class-wide."""
        if cls._images_loaded:
            return

        # Define filenames expected in assets/images/
        # Checkouts usually have specific graphics per direction
        p_n_l = IMAGE_DIR / "kasse_l.png"  # Normal Left
        p_n_r = IMAGE_DIR / "kasse_r.png"  # Normal Right
        p_s_l = IMAGE_DIR / "sb_l.png"  # SB Left
        p_s_r = IMAGE_DIR / "sb_r.png"  # SB Right

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
        return QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        # 1. Determine which image to use
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

        # 2. Draw Image or Fallback
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                CHECKOUT_WIDTH,
                CHECKOUT_HEIGHT,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.drawPixmap(0, 0, scaled)
        else:
            # Fallback: Grey Box
            color = (
                QColor("#607D8B")
                if self.c_type == "Normal"
                else QColor("#455A64")
            )
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(rect)

            # Indicator for direction
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            painter.setPen(Qt.PenStyle.NoPen)
            if self.orientation == "Left":
                painter.drawRect(0, 0, 5, CHECKOUT_HEIGHT)
            else:
                painter.drawRect(CHECKOUT_WIDTH - 5, 0, 5, CHECKOUT_HEIGHT)

            # Text for type if no image
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.c_type)

        # 3. Selection Highlight
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QPen(COLOR_SELECTION, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))

        # 4. Status Light (Open/Closed)
        if self.show_light:
            status_color = (
                Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
            )
            painter.setBrush(QBrush(status_color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            # Draw light at offset position
            lx, ly = self.light_offset
            # If offset is list/tuple
            if isinstance(lx, (list, tuple)):
                lx, ly = lx[0], lx[1]

            painter.drawEllipse(int(lx), int(ly), 8, 8)

        # 5. ID Overlay
        if self.data_id is not None:
            font = QFont()
            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)

            # Text shadow
            painter.setPen(QPen(Qt.GlobalColor.black))
            text_rect = rect.adjusted(2, 2, 2, 2)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
                f"#{self.data_id}",
            )

            # Text foreground
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
