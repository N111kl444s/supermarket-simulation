"""
Custom graphics view module.
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
        """
        Initializes the view.

        @param scene: The graphics scene to display.
        @type scene: QGraphicsScene
        @param parent: Parent widget.
        @type parent: QWidget
        """
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scrollbars: Allow navigation when zoomed in
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Interaction: Allow dragging the map with the mouse
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Zoom logic: Zoom towards the mouse cursor
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse
        )
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setMouseTracking(True)

        # Flag to track if user has interfered with the auto-fit
        self._is_manually_zoomed = False

    def wheelEvent(self, event: QWheelEvent):
        """
        Handles mouse wheel events to zoom in and out with limits.
        Disables auto-fit mode.

        @param event: Wheel event.
        @type event: QWheelEvent
        """
        # Mark as manually zoomed -> disable AutoFit in resizeEvent
        self._is_manually_zoomed = True

        zoom_factor = 1.15

        # Current Scale Factor (m11 is horizontal scale)
        current_scale = self.transform().m11()

        if event.angleDelta().y() > 0:
            # Zoom In
            # Optional: Max Zoom Limit (e.g., 5.0x)
            if current_scale < 5.0:
                self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom Out
            # Limit: Do not zoom out if scale is too small (e.g., 0.5x)
            # Adjust '0.1' or '0.5' based on how small you want it to go.
            # 0.5 means 50% of original size (1 pixel = 0.5 screen pixels)
            if current_scale > 0.2:
                self.scale(1 / zoom_factor, 1 / zoom_factor)

        # Accept event to prevent default scrolling
        event.accept()

    def resizeEvent(self, e):
        """
        Handles resize events.
        Only applies Auto-Fit if the user hasn't zoomed manually.

        @param e: Resize event.
        @type e: QResizeEvent
        """
        super().resizeEvent(e)

        # If user is zooming manually, do NOT reset the view
        if self._is_manually_zoomed:
            return

        if self.scene() and not self.sceneRect().isEmpty():
            self._apply_auto_fit()

    def reset_zoom(self):
        """
        Resets the view to Auto-Fit mode (showing the whole map or target quadrant).
        """
        self._is_manually_zoomed = False
        self._apply_auto_fit()

    def _apply_auto_fit(self):
        """
        Internal method to fit the scene or quadrant into the view.
        """
        mw = self.window()
        # Check for specific Quadrant 1 Zoom
        if (
            mw
            and hasattr(mw, "is_q1_maximized")
            and mw.is_q1_maximized
            and hasattr(mw, "item_q1")
            and mw.item_q1
        ):
            self.fitInView(
                mw.item_q1.boundingRect(),
                Qt.AspectRatioMode.KeepAspectRatio,
            )
        else:
            # Fit whole scene
            self.fitInView(
                self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
