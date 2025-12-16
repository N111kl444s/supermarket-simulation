"""
Custom graphics view module.
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter


class AutoFitGraphicsView(QGraphicsView):
    """
    A QGraphicsView that automatically scales its content to fit the view.
    Also handles specific zoom logic for Quadrant 1 (checkout area).
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
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

    def resizeEvent(self, e):
        """
        Handles resize events to adjust the zoom level.

        @param e: Resize event.
        @type e: QResizeEvent
        """
        super().resizeEvent(e)
        if self.scene() and not self.sceneRect().isEmpty():
            mw = self.window()
            # Dynamic check to see if we should zoom into Quadrant 1
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
                self.fitInView(
                    self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
                )
