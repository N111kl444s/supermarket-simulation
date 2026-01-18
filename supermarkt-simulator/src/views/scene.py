"""
Graphics Scene for the editor.
Handles mouse events for drawing areas and forwarding clicks.
Refactored: Robust Fallback for Item Clicking.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor
from config import COLOR_WAITING_AREA, COLOR_START_AREA, COLOR_EXIT_AREA
from views.items.shelf_item import ShelfItem
from views.items.checkout_item import CheckoutItem

class RouteEditorScene(QGraphicsScene):
    # Signals
    clicked_point = pyqtSignal(QPointF)
    waiting_area_created = pyqtSignal(QRectF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None
        
        # Temporary item for drawing rectangles (rubberband)
        self.temp_rect_item = None
        self.start_point = None

    def mousePressEvent(self, event):
        # 1. Standard-Verarbeitung (Items klicken)
        super().mousePressEvent(event)
        
        # 2. Wurde Klick verbraucht?
        if event.isAccepted():
            return

        # FAIL-SAFE: Wenn super() das Item nicht getroffen hat (z.B. wegen Layering),
        # suchen wir manuell danach.
        if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
            items_at_pos = self.items(event.scenePos())
            for item in items_at_pos:
                # Prüfen auf unsere interaktiven Items
                if isinstance(item, (ShelfItem, CheckoutItem)):
                    # Klick manuell auslösen
                    item.mousePressEvent(event)
                    if event.isAccepted():
                        return

        # 3. Wenn immer noch nicht akzeptiert -> Zeichnen oder Platzieren
        if not self.main_window:
            return

        pos = event.scenePos()
        is_wa = getattr(self.main_window, 'is_drawing_waiting_area', False)
        is_sa = getattr(self.main_window, 'is_drawing_start_area', False)
        is_ea = getattr(self.main_window, 'is_drawing_exit_area', False)

        if event.button() == Qt.MouseButton.LeftButton:
            if is_wa or is_sa or is_ea:
                # Start Drawing Area
                self.start_point = pos
                self.temp_rect_item = QGraphicsRectItem()
                
                color = QColor(0, 0, 0)
                if is_wa: color = COLOR_WAITING_AREA
                elif is_sa: color = COLOR_START_AREA
                elif is_ea: color = COLOR_EXIT_AREA
                
                self.temp_rect_item.setBrush(QBrush(color))
                self.temp_rect_item.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
                self.addItem(self.temp_rect_item)
                event.accept()
            else:
                # Platzierungssignal für neue Objekte
                self.clicked_point.emit(pos)

    def mouseMoveEvent(self, event):
        if self.temp_rect_item and self.start_point:
            current_pos = event.scenePos()
            rect = QRectF(self.start_point, current_pos).normalized()
            self.temp_rect_item.setRect(rect)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.temp_rect_item and self.start_point:
            final_rect = self.temp_rect_item.rect()
            self.removeItem(self.temp_rect_item)
            self.temp_rect_item = None
            self.start_point = None
            
            if final_rect.width() > 5 and final_rect.height() > 5:
                self.waiting_area_created.emit(final_rect)
            event.accept()
        else:
            super().mouseReleaseEvent(event)