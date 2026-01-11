"""
Custom graphics view module.
Refactored: Smart zoom limits relative to window size.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QWheelEvent


class AutoFitGraphicsView(QGraphicsView):
    """
    A QGraphicsView that automatically scales its content to fit the view,
    but allows manual zooming and panning.
    """

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scrollbars: Allow navigation when zoomed in
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Interaction
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Zoom logic
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setMouseTracking(True)

        self._is_manually_zoomed = False

    def wheelEvent(self, event: QWheelEvent):
        """
        Handles mouse wheel events with dynamic limits.
        """
        self._is_manually_zoomed = True
        zoom_factor = 1.15
        current_scale = self.transform().m11()

        # Berechne den Skalierungsfaktor, wenn die Map perfekt eingepasst wäre
        fit_scale = self._calculate_fit_scale()
        
        # Limit: Maximal 1 Stufe weiter raus als "Fit" (ca. 85% der Fit-Größe)
        min_allowed_scale = fit_scale * 0.85 

        if event.angleDelta().y() > 0:
            # Zoom In (Rein) - Limit 5.0x
            if current_scale < 5.0:
                self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom Out (Raus) - Dynamisches Limit
            new_scale = current_scale / zoom_factor
            if new_scale >= min_allowed_scale:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
            else:
                # Wenn wir zu weit raus wären, setzen wir auf das Minimum zurück (optional)
                # Oder machen einfach nichts. Hier: Nichts tun.
                pass

        event.accept()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._is_manually_zoomed:
            return
        if self.scene() and not self.sceneRect().isEmpty():
            self._apply_auto_fit()

    def reset_zoom(self):
        """Resets to Auto-Fit."""
        self._is_manually_zoomed = False
        self._apply_auto_fit()

    def _calculate_fit_scale(self):
        """Calculates the scale factor if the scene were fitted right now."""
        if not self.scene() or self.sceneRect().isEmpty():
            return 1.0
            
        vp = self.viewport().rect()
        scene = self.sceneRect()
        
        ratio_w = vp.width() / scene.width()
        ratio_h = vp.height() / scene.height()
        
        return min(ratio_w, ratio_h)

    def _apply_auto_fit(self):
        mw = self.window()
        # Quadrant 1 Zoom Logic
        if (mw and hasattr(mw, "is_q1_maximized") and mw.is_q1_maximized 
            and hasattr(mw, "item_q1") and mw.item_q1):
            self.fitInView(mw.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)