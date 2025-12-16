"""
Simulation scene module.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import pyqtSignal, Qt, QRectF, QPointF
from PyQt6.QtGui import QPen
from config import *


class RouteEditorScene(QGraphicsScene):
    """
    Enhanced QGraphicsScene that supports admin interaction modes (drawing routes, placing objects).

    @ivar clicked_point: Signal emitted when a point is clicked in admin mode.
    @type clicked_point: pyqtSignal(QPointF)
    @ivar waiting_area_created: Signal emitted when a waiting area rectangle is drawn.
    @type waiting_area_created: pyqtSignal(QRectF)
    """

    clicked_point = pyqtSignal(QPointF)
    waiting_area_created = pyqtSignal(QRectF)

    def __init__(self, p=None):
        """
        Initializes the scene.

        @param p: Parent object.
        """
        super().__init__(p)
        self.main_window = None
        self.rect_start = None
        self.temp_rect = None

    def mousePressEvent(self, e):
        """
        Handles mouse press events to capture admin inputs.

        @param e: Mouse event.
        @type e: QGraphicsSceneMouseEvent
        """
        if self.main_window and self.main_window.is_admin_mode:
            super().mousePressEvent(e)
            if self.selectedItems():
                return
            if (
                self.main_window.is_drawing_waiting_area
                and e.button() == Qt.MouseButton.LeftButton
            ):
                self.rect_start = e.scenePos()
                self.temp_rect = QGraphicsRectItem()
                self.temp_rect.setPen(
                    QPen(COLOR_GREEN, 2, Qt.PenStyle.DashLine)
                )
                self.addItem(self.temp_rect)
                e.accept()
                return
            if (
                self.main_window.is_drawing_mode
                or self.main_window.is_placing_shelves
                or self.main_window.is_placing_checkout
            ) and e.button() == Qt.MouseButton.LeftButton:
                if self.sceneRect().contains(e.scenePos()):
                    self.clicked_point.emit(e.scenePos())
                    e.accept()
                    return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        """
        Handles mouse move events (e.g., for rubber-banding rectangles).

        @param e: Mouse event.
        """
        if (
            self.main_window.is_drawing_waiting_area
            and self.rect_start
            and self.temp_rect
        ):
            self.temp_rect.setRect(
                QRectF(self.rect_start, e.scenePos()).normalized()
            )
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        Handles mouse release events to finalize drawing actions.

        @param e: Mouse event.
        """
        if self.main_window.is_drawing_waiting_area and self.rect_start:
            self.waiting_area_created.emit(
                QRectF(self.rect_start, e.scenePos()).normalized()
            )
            self.removeItem(self.temp_rect)
            self.rect_start = None
            e.accept()
            return
        super().mouseReleaseEvent(e)
