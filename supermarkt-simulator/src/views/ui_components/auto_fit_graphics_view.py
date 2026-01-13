"""
Custom graphics view module.
Refactored: 
- Supports 'centerOn' target point in reset_zoom.
- Correct user-defined zoom limits.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QWheelEvent


class AutoFitGraphicsView(QGraphicsView):
    
    FIXED_ZOOM_LEVEL = 3.21413934

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)

        self._is_manually_zoomed = False

    def wheelEvent(self, event: QWheelEvent):
        self._is_manually_zoomed = True
        zoom_factor = 1.15
        current_scale = self.transform().m11()

        # MIN ZOOM OUT (1.38956114)
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

    def resizeEvent(self, e):
        super().resizeEvent(e)

    def reset_zoom(self, center_point=None):
        """
        Resets to fixed standard zoom.
        Optional: centers on 'center_point' (QPointF).
        """
        self._is_manually_zoomed = False
        self.resetTransform()
        self.scale(self.FIXED_ZOOM_LEVEL, self.FIXED_ZOOM_LEVEL)
        
        if center_point:
            self.centerOn(center_point)
        elif self.scene():
            self.centerOn(self.scene().sceneRect().center())