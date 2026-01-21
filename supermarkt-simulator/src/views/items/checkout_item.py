"""
Visual representation of a checkout counter.
Refactored:
- FIX: High-Quality Rendering. Uses transformation scaling instead of pixmap resizing to prevent pixelation.
- Supports different checkout types (Normal/SB).
- Renders optional cashier (Azubi/Profi) and lights.
"""

from PyQt6.QtWidgets import (
    QGraphicsItemGroup,
    QGraphicsPixmapItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsItem,
)
from PyQt6.QtGui import QPixmap, QBrush, QPen, QTransform
from PyQt6.QtCore import Qt
from config import *
from .cashier_item import CashierItem


class CheckoutItem(QGraphicsItemGroup):
    def __init__(
        self, data, map_manager, width=100, height=100, cashier_size=10
    ):
        super().__init__()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.data = data
        self.map_mgr = map_manager

        # Zielgröße
        self.target_width = width
        self.target_height = height
        self.cashier_size = cashier_size

        self.cid = data["id"]
        self.c_type = data.get("type", "Normal")
        self.orientation = data.get("orientation", "Right")
        self.is_open = data.get("open", True)
        self.is_broken = False

        # Visual elements
        self.checkout_bg = None
        self.cashier_item = None
        self.light_item = None

        self.blink_state = False
        self.click_callback = None

        self._load_images()
        self.create_visuals()
        self.set_status(self.is_open)

        self.setPos(data["x"], data["y"])

        angle = data.get("angle", 0)
        if angle != 0:
            self.setRotation(angle)

    def set_callback(self, func):
        self.click_callback = func

    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback(self)
        super().mousePressEvent(event)

    @classmethod
    def _load_images(cls):
        pass

    def create_visuals(self):
        self.checkout_bg = QGraphicsPixmapItem()

        img_name = "sb.png" if self.c_type == "SB" else "kasse.png"

        pix = QPixmap()
        p = IMAGE_DIR / img_name
        if p.exists():
            pix.load(str(p))

        if not pix.isNull():
            # FIX: High Quality Scaling
            # Wir behalten die Original-Pixmap und skalieren das Item via Transform
            self.checkout_bg.setPixmap(pix)

            # Berechne Skalierungsfaktor
            scale_x = self.target_width / pix.width()
            scale_y = self.target_height / pix.height()

            # Transformation anwenden
            transform = QTransform()
            transform.scale(scale_x, scale_y)
            self.checkout_bg.setTransform(transform)

            # Filter-Modus für bessere Qualität beim Zoomen
            self.checkout_bg.setTransformationMode(
                Qt.TransformationMode.SmoothTransformation
            )

            self.addToGroup(self.checkout_bg)
        else:
            # Fallback
            rect = QGraphicsRectItem(
                0, 0, self.target_width, self.target_height
            )
            rect.setBrush(QBrush(COLOR_CHECKOUT))
            self.addToGroup(rect)

    def update_cashier(self):
        if self.cashier_item:
            self.removeFromGroup(self.cashier_item)
            self.cashier_item = None

        if self.c_type == "SB":
            return

        if not self.is_open:
            return

        self.cashier_item = CashierItem(self.data, size=self.cashier_size)

        # Positionierung (relativ zur Zielgröße)
        cx = self.target_width * 0.42
        cy = self.target_height * 0.20

        self.cashier_item.setPos(cx, cy)
        self.addToGroup(self.cashier_item)

    def set_status(self, is_open):
        self.is_open = is_open
        self.update_cashier()
        self.update_light()

    def set_broken(self, is_broken):
        self.is_broken = is_broken
        self.update_light()

    def blink_light(self):
        if self.is_broken:
            self.blink_state = not self.blink_state
            self.update_light()

    def update_light(self):
        if self.light_item:
            self.removeFromGroup(self.light_item)
            self.light_item = None

        r = max(2, self.target_width * 0.15)  # Etwas größer für Sichtbarkeit
        lx = self.target_width * 0.08
        ly = self.target_height * 0.70

        self.light_item = QGraphicsEllipseItem(0, 0, r, r)
        self.light_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.light_item.setPos(lx, ly)

        if self.is_broken:
            if self.blink_state:
                self.light_item.setBrush(QBrush(COLOR_WARNING))
            else:
                self.light_item.setBrush(QBrush(Qt.GlobalColor.black))
        elif self.is_open:
            self.light_item.setBrush(QBrush(COLOR_SUCCESS))
        else:
            self.light_item.setBrush(QBrush(COLOR_ERROR))

        self.addToGroup(self.light_item)
