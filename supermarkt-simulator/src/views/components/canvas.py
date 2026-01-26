"""
Simulation Canvas Component.
Refactored:
- ADJUST: Increased default start zoom to 2.5x ("Closer to shop").
- LOGIC: Zoom limit constrained by HEIGHT ratio (prevents top/bottom borders).
- LOGIC: Allows horizontal panning.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt, QPoint, QRectF
from PyQt6.QtGui import QPainter, QMouseEvent, QCursor
from views.scene import SimulationScene


class SimulationCanvas(QGraphicsView):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.sim_scene = SimulationScene(self)
        self.setScene(self.sim_scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.zoom_level = 1.0
        self.zoom_max = 1000.0

        self._is_panning = False
        self._pan_start_pos = QPoint()

    def set_drawing_cursor(self, active):
        if active:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _get_min_zoom_level(self):
        """
        Berechnet den minimalen Zoom basierend NUR auf der HÖHE.
        Das verhindert schwarze Ränder oben und unten, erlaubt aber Panning links/rechts.
        """
        scene_rect = self.scene().sceneRect()
        view_rect = self.viewport().rect()

        if scene_rect.height() == 0:
            return 0.1

        # min_zoom = Fensterhöhe / Bildhöhe
        height_ratio = view_rect.height() / scene_rect.height()

        return height_ratio

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        current_min = self._get_min_zoom_level()

        if event.angleDelta().y() > 0:
            # Zoom In
            target_zoom = self.zoom_level * zoom_in_factor
            if target_zoom > self.zoom_max:
                target_zoom = self.zoom_max
            factor = target_zoom / self.zoom_level
        else:
            # Zoom Out
            target_zoom = self.zoom_level * zoom_out_factor

            # LIMIT: Nicht kleiner als die Fensterhöhe zulässt
            if target_zoom < current_min:
                target_zoom = current_min

            factor = target_zoom / self.zoom_level

        self.scale(factor, factor)
        self.zoom_level = target_zoom

    def reset_zoom(self, center_point=None):
        """
        Setzt Kamera zurück.
        Ziel: 2.5x Zoom (250%), damit man direkt Details (Laden) sieht.
        Aber niemals kleiner als 'min_zoom' (keine schwarzen Ränder).
        """
        self.resetTransform()

        min_zoom = self._get_min_zoom_level()

        # HIER DIE ÄNDERUNG: Standard ist jetzt 2.5 (viel näher)
        target_zoom = max(2.5, min_zoom)

        self.scale(target_zoom, target_zoom)
        self.zoom_level = target_zoom

        if center_point:
            self.centerOn(center_point)
        else:
            sr = self.scene().sceneRect()
            self.centerOn(sr.center())

    # --- MOUSE EVENTS ---

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        mw = self.main_window
        if event.button() == Qt.MouseButton.LeftButton:
            if (
                mw.is_drawing_waiting_area
                or mw.is_drawing_start_area
                or mw.is_drawing_exit_area
            ):

                pos = self.mapToScene(event.pos())
                self.sim_scene.start_drawing_area(pos)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.pos() - self._pan_start_pos
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            self._pan_start_pos = event.pos()
            event.accept()
            return

        mw = self.main_window
        if (
            mw.is_drawing_waiting_area
            or mw.is_drawing_start_area
            or mw.is_drawing_exit_area
        ):

            if self.sim_scene.temp_rect_item:
                pos = self.mapToScene(event.pos())
                self.sim_scene.update_drawing_area(pos)
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            mw = self.main_window
            is_drawing = (
                mw.is_drawing_waiting_area
                or mw.is_drawing_start_area
                or mw.is_drawing_exit_area
            )
            self.set_drawing_cursor(is_drawing)
            event.accept()
            return

        mw = self.main_window
        if event.button() == Qt.MouseButton.LeftButton:
            if (
                mw.is_drawing_waiting_area
                or mw.is_drawing_start_area
                or mw.is_drawing_exit_area
            ):

                self.sim_scene.finish_drawing_area()
                return

        super().mouseReleaseEvent(event)
