"""
Custom graphics view module.
Refactored:
- STRICT Middle Mouse Panning.
- UNCONDITIONAL pass-through for Left/Right clicks to the Scene/Items.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QWheelEvent, QMouseEvent

class AutoFitGraphicsView(QGraphicsView):
    
    FIXED_ZOOM_LEVEL = 3.21413934

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)

        self._is_manually_zoomed = False
        self._is_panning = False
        self._last_pan_pos = QPoint()

    def wheelEvent(self, event: QWheelEvent):
        self._is_manually_zoomed = True
        zoom_factor = 1.15
        current_scale = self.transform().m11()
        min_allowed_scale = 1.38956114

        if event.angleDelta().y() > 0:
            if current_scale < 50.0:
                self.scale(zoom_factor, zoom_factor)
        else:
            new_scale = current_scale / zoom_factor
            if new_scale >= min_allowed_scale:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
            elif current_scale > min_allowed_scale:
                factor = min_allowed_scale / current_scale
                self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        # Pass clicks to Scene -> Items
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning and event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def reset_zoom(self, center_point=None):
        self._is_manually_zoomed = False
        self.resetTransform()
        self.scale(self.FIXED_ZOOM_LEVEL, self.FIXED_ZOOM_LEVEL)
        if center_point:
            self.centerOn(center_point)
        elif self.scene():
            self.centerOn(self.scene().sceneRect().center())