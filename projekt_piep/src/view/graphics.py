# src/view/graphics.py

from typing import Optional  # <-- DIESER IMPORT FEHLTE
from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QBrush, QPen, QPixmap

# Absolute imports
from view.styles import Colors, Dimensions, Fonts
from settings import IMAGE_DIR


class CustomerSprite(QGraphicsObject):
    """
    Visualizes the customer exactly like the original:
    - Pink circle
    - Number of items inside
    - Green arc progress bar when scanning
    """

    def __init__(self, customer_id: int):
        super().__init__()
        self.customer_id = customer_id

        # Local state for rendering
        self.item_text = "0"
        self.is_scanning = False
        self.scan_progress = 0.0  # 0.0 to 1.0

        self.setZValue(20)  # High Z-Index like original

    def boundingRect(self) -> QRectF:
        s = Dimensions.CUSTOMER_SIZE
        # Kleiner Puffer für den Zeichenstift
        return QRectF(-s / 2 - 2, -s / 2 - 2, s + 4, s + 4)

    def paint(self, painter: QPainter, option, widget=None):
        # 1. Base Circle (Pink)
        r = Dimensions.CUSTOMER_SIZE
        rect = QRectF(-r / 2, -r / 2, r, r)

        painter.setBrush(QBrush(Colors.CUSTOMER))
        painter.setPen(QPen(Colors.WHITE, 1))
        painter.drawEllipse(rect)

        # 2. Item Count Text
        painter.setPen(Colors.WHITE)
        painter.setFont(Fonts.customer_text())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.item_text)

        # 3. Scanning Progress Arc (The "Cool Feature")
        if self.is_scanning:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(Colors.SCAN_PROGRESS, 2))

            # PyQt drawArc uses 1/16th of a degree steps
            # Full circle = 360 * 16
            span_angle = int(self.scan_progress * 360 * 16)

            # Start at 90 degrees (Top) -> 90 * 16
            # Negative span for clockwise direction
            painter.drawArc(rect.adjusted(-2, -2, 2, 2), 90 * 16, -span_angle)

    def update_state(
        self, items_left: int, is_scanning: bool, progress: float
    ):
        """Called by Controller to update visuals."""
        self.item_text = str(items_left)
        self.is_scanning = is_scanning
        self.scan_progress = progress
        self.update()


class CheckoutLaneSprite(QGraphicsObject):
    """
    Visualizes the checkout. Supports Images or Fallback-Drawing.
    """

    _pixmap_normal_left = None
    _pixmap_normal_right = None
    _pixmap_sb_left = None
    _pixmap_sb_right = None

    def __init__(
        self, lane_id: int, x: float, y: float, type_str: str, orientation: str
    ):
        super().__init__()
        self.lane_id = lane_id
        self.type_str = type_str  # "Normal" or "SB"
        self.orientation = orientation
        self.setPos(x, y)
        self.setZValue(6)

        self._load_images()

    def _load_images(self):
        # Lazy loading of images
        if CheckoutLaneSprite._pixmap_normal_right is None:
            try:
                # Versuche Bilder zu laden (Pfade müssen stimmen!)
                CheckoutLaneSprite._pixmap_normal_right = QPixmap(
                    str(IMAGE_DIR / "checkout_right.png")
                )
                CheckoutLaneSprite._pixmap_normal_left = QPixmap(
                    str(IMAGE_DIR / "checkout_left.png")
                )
                CheckoutLaneSprite._pixmap_sb_right = QPixmap(
                    str(IMAGE_DIR / "sb_checkout_right.png")
                )
                CheckoutLaneSprite._pixmap_sb_left = QPixmap(
                    str(IMAGE_DIR / "sb_checkout_left.png")
                )
            except Exception:
                pass

    def boundingRect(self) -> QRectF:
        return QRectF(
            0, 0, Dimensions.CHECKOUT_WIDTH, Dimensions.CHECKOUT_HEIGHT
        )

    def paint(self, painter: QPainter, option, widget=None):
        pixmap = self._get_pixmap()

        if pixmap and not pixmap.isNull():
            painter.drawPixmap(self.boundingRect().toRect(), pixmap)
        else:
            # Fallback Drawing (Sieht aus wie im Original-Code fallback)
            color = Colors.get_checkout_color(self.type_str)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Colors.BLACK))
            painter.drawRect(self.boundingRect())

            # Kleiner Streifen für Orientierung
            painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
            painter.setPen(Qt.PenStyle.NoPen)
            if self.orientation == "Left":
                painter.drawRect(0, 0, 5, Dimensions.CHECKOUT_HEIGHT)
            else:
                painter.drawRect(
                    Dimensions.CHECKOUT_WIDTH - 5,
                    0,
                    5,
                    Dimensions.CHECKOUT_HEIGHT,
                )

        # ID darüber zeichnen
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            self.boundingRect(),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
            f"#{self.lane_id}",
        )

    def _get_pixmap(self) -> Optional[QPixmap]:
        if self.type_str == "SB":
            return (
                self._pixmap_sb_left
                if self.orientation == "Left"
                else self._pixmap_sb_right
            )
        return (
            self._pixmap_normal_left
            if self.orientation == "Left"
            else self._pixmap_normal_right
        )
