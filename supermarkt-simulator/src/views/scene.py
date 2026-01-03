"""
Graphics Scene for the editor.
Handles mouse events for drawing areas (rectangles) and placing points.
Refactored: Supports Exit Area drawing and Route clicking.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor
from config import COLOR_WAITING_AREA, COLOR_START_AREA, COLOR_EXIT_AREA

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
        if not self.main_window:
            super().mousePressEvent(event)
            return

        pos = event.scenePos()

        # Check which Area tool is active
        is_wa = self.main_window.is_drawing_waiting_area
        is_sa = self.main_window.is_drawing_start_area
        is_ea = self.main_window.is_drawing_exit_area # NEU

        if event.button() == Qt.MouseButton.LeftButton:
            if is_wa or is_sa or is_ea:
                # Start drawing a rectangle
                self.start_point = pos
                self.temp_rect_item = QGraphicsRectItem()
                
                # Determine color
                color = QColor(0, 0, 0)
                if is_wa: color = COLOR_WAITING_AREA
                elif is_sa: color = COLOR_START_AREA
                elif is_ea: color = COLOR_EXIT_AREA
                
                self.temp_rect_item.setBrush(QBrush(color))
                self.temp_rect_item.setPen(QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
                self.addItem(self.temp_rect_item)
            else:
                # If strictly not selecting (e.g. placing items or points), emit click
                # We assume if dragging isn't the goal, it's a click
                self.clicked_point.emit(pos)
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.temp_rect_item and self.start_point:
            current_pos = event.scenePos()
            rect = QRectF(self.start_point, current_pos).normalized()
            self.temp_rect_item.setRect(rect)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.temp_rect_item and self.start_point:
            # Finish drawing rectangle
            final_rect = self.temp_rect_item.rect()
            
            # Remove temp item (Controller creates the real persistent item)
            self.removeItem(self.temp_rect_item)
            self.temp_rect_item = None
            self.start_point = None
            
            if final_rect.width() > 5 and final_rect.height() > 5:
                self.waiting_area_created.emit(final_rect)
        
        super().mouseReleaseEvent(event)