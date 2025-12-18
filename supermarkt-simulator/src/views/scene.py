"""
Graphics Scene module handling interactivity.
Refactored: Supports drawing both Waiting Area (Blue) and Start Area (Green).
"""

from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsSceneMouseEvent,
    QGraphicsRectItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPen, QColor, QBrush
from config import COLOR_WAITING_AREA, COLOR_START_AREA, COLOR_SELECTION


class RouteEditorScene(QGraphicsScene):
    """
    Custom GraphicsScene to handle map interactions.
    """

    clicked_point = pyqtSignal(QPointF)
    waiting_area_created = pyqtSignal(
        QRectF
    )  # Used for both areas, Controller distinguishes via Tool

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None

        # Drawing State
        self.rect_start_point = None
        self.current_drawing_item = None

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check active modes from MainWindow
            if self.main_window:
                if (
                    self.main_window.is_drawing_waiting_area
                    or self.main_window.is_drawing_start_area
                ):
                    self.rect_start_point = event.scenePos()
                    self.current_drawing_item = QGraphicsRectItem()

                    # Distinguish Colors
                    if self.main_window.is_drawing_start_area:
                        self.current_drawing_item.setBrush(
                            QBrush(COLOR_START_AREA)
                        )
                        self.current_drawing_item.setPen(
                            QPen(
                                Qt.GlobalColor.darkGreen,
                                1,
                                Qt.PenStyle.DashLine,
                            )
                        )
                    else:
                        self.current_drawing_item.setBrush(
                            QBrush(COLOR_WAITING_AREA)
                        )
                        self.current_drawing_item.setPen(
                            QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine)
                        )

                    self.addItem(self.current_drawing_item)
                    return  # Consume event

                if (
                    self.main_window.is_drawing_mode
                    or self.main_window.is_placing_shelves
                    or self.main_window.is_placing_checkout
                ):
                    self.clicked_point.emit(event.scenePos())
                    return  # Consume event

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if self.rect_start_point and self.current_drawing_item:
            current_pos = event.scenePos()
            rect = QRectF(self.rect_start_point, current_pos).normalized()
            self.current_drawing_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.rect_start_point
            and self.current_drawing_item
        ):
            rect = self.current_drawing_item.rect()
            self.removeItem(self.current_drawing_item)
            self.current_drawing_item = None
            self.rect_start_point = None

            # Emit signal with valid rect
            if rect.width() > 5 and rect.height() > 5:
                self.waiting_area_created.emit(rect)
        else:
            super().mouseReleaseEvent(event)
