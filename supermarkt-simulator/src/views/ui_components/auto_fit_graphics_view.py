"""
Custom graphics view.
Refactored: 
- Robust detection of selectable items using scene().items().
- Ensures Right-Click always passes through to items.
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsItem
from PyQt6.QtCore import Qt
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
        # RECHTSKLICK: Immer durchlassen (Bearbeiten)
        if event.button() == Qt.MouseButton.RightButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._is_panning = False
            super().mousePressEvent(event)
            return

        # LINKSKLICK: Prüfen, ob wir auswählen oder ziehen wollen
        if event.button() == Qt.MouseButton.LeftButton:
            pos = self.mapToScene(event.pos())
            
            # WICHTIG: Wir prüfen ALLE Items an dieser Stelle, nicht nur das oberste!
            items_at_pos = self.scene().items(pos, Qt.ItemSelectionMode.IntersectsItemShape, Qt.SortOrder.DescendingOrder, self.transform())
            
            is_interactive = False
            
            for item in items_at_pos:
                # Prüfe Item und seine Eltern (wichtig bei Gruppen/Labels)
                checker = item
                while checker:
                    if checker.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable:
                        is_interactive = True
                        break
                    checker = checker.parentItem()
                
                if is_interactive:
                    break
            
            if is_interactive:
                # Wählbares Item getroffen -> Klicken/Selektieren
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                self._is_panning = False
                super().mousePressEvent(event) # Event weitergeben!
            else:
                # Leerraum -> Verschieben
                self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                self._is_panning = True
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        if self._is_panning:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._is_panning = False

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