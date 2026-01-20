"""
Visual representation of a checkout counter.
Refactored:
- Supports different checkout types (Normal/SB).
- Renders optional cashier (Azubi/Profi).
- Renders status lights (Green/Red) and queues.
- NEW: Added support for 'Yellow' blinking light during maintenance.
- FIX: Added QObject inheritance and 'clicked' signal.
"""

from PyQt6.QtWidgets import (
    QGraphicsItemGroup,
    QGraphicsPixmapItem,
    QGraphicsSimpleTextItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsItem
)
from PyQt6.QtGui import QPixmap, QColor, QBrush, QPen, QTransform
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from config import *
from .cashier_item import CashierItem

# Erbt von QObject (für Signale) und QGraphicsItemGroup (für die Grafik)
class CheckoutItem(QObject, QGraphicsItemGroup):
    clicked = pyqtSignal(object)

    _pixmaps = {}
    _loaded = False

    def __init__(self, data, map_manager):
        QObject.__init__(self)
        QGraphicsItemGroup.__init__(self)
        
        # Wichtig für die Interaktion:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable)

        self.data = data
        self.map_mgr = map_manager
        
        self.cid = data["id"]
        self.c_type = data.get("type", "Normal") # Normal, SB
        self.orientation = data.get("orientation", "Right") # Left, Right
        self.is_open = data.get("open", True)
        self.is_broken = False # NEW: Maintenance Status

        # Visual elements
        self.checkout_bg = None
        self.cashier_item = None
        self.light_item = None
        
        self.blink_state = False # For yellow blinking

        self._load_images()
        self.create_visuals()
        self.set_status(self.is_open)
        
        # Initial pos
        self.setPos(data["x"], data["y"])
        
        angle = data.get("angle", 0)
        if angle != 0:
            self.setRotation(angle)

    def mousePressEvent(self, event):
        """Klick-Event an Controller weiterleiten."""
        self.clicked.emit(self)
        super().mousePressEvent(event)

    @classmethod
    def _load_images(cls):
        if cls._loaded:
            return
        pass

    def create_visuals(self):
        # 1. Base Image
        self.checkout_bg = QGraphicsPixmapItem()
        
        img_name = "sb.png" if self.c_type == "SB" else "kasse.png"
        
        pix = QPixmap()
        p = IMAGE_DIR / img_name
        if p.exists():
            pix.load(str(p))
        
        if not pix.isNull():
            self.checkout_bg.setPixmap(pix)
            self.addToGroup(self.checkout_bg)
        else:
            # Fallback Shape
            rect = QGraphicsRectItem(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)
            rect.setBrush(QBrush(COLOR_CHECKOUT))
            self.addToGroup(rect)

    def update_cashier(self):
        """Update or create cashier visual."""
        # Remove old if exists
        if self.cashier_item:
            self.removeFromGroup(self.cashier_item)
            self.cashier_item = None
            
        if self.c_type == "SB":
            return # No cashier for SB usually
            
        if not self.is_open:
            return # No cashier if closed
            
        # Create Cashier
        self.cashier_item = CashierItem(self.data, size=32)
        
        # Position relative to checkout (approximate center/top)
        cx = 50 
        cy = 20 
        
        self.cashier_item.setPos(cx, cy)
        self.addToGroup(self.cashier_item)

    def set_status(self, is_open):
        self.is_open = is_open
        self.update_cashier()
        self.update_light()

    def set_broken(self, is_broken):
        """NEW: Set maintenance status."""
        self.is_broken = is_broken
        self.update_light()

    def blink_light(self):
        """Called by timer/tick if broken."""
        if self.is_broken:
            self.blink_state = not self.blink_state
            self.update_light()

    def update_light(self):
        if self.light_item:
            self.removeFromGroup(self.light_item)
            self.light_item = None
            
        # Light size
        r = 12
        
        # Pos based on type/orientation
        lx = 10
        ly = 80
        
        self.light_item = QGraphicsEllipseItem(0, 0, r, r)
        self.light_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.light_item.setPos(lx, ly)
        
        if self.is_broken:
            # Yellow Blinking
            if self.blink_state:
                self.light_item.setBrush(QBrush(COLOR_WARNING)) # Yellow
            else:
                self.light_item.setBrush(QBrush(Qt.GlobalColor.black)) # Off
        elif self.is_open:
            self.light_item.setBrush(QBrush(COLOR_SUCCESS)) # Green
        else:
            self.light_item.setBrush(QBrush(COLOR_ERROR)) # Red
            
        self.addToGroup(self.light_item)