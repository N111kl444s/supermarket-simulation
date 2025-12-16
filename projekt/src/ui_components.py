from PyQt6.QtWidgets import (
    QGroupBox,
    QGraphicsObject,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
)
from PyQt6.QtCore import pyqtSignal, Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen
from config import *


class ClickableGroupBox(QGroupBox):
    clicked = pyqtSignal()

    def __init__(self, t, p=None):
        super().__init__(t, p)

    def mousePressEvent(self, e):
        (
            self.clicked.emit()
            if e.button() == Qt.MouseButton.LeftButton
            else None
        )
        super().mousePressEvent(e)


class ClickablePixmapItem(QGraphicsObject):
    clicked = pyqtSignal()

    def __init__(self, p, par=None):
        super().__init__(par)
        self.pixmap = p

    def boundingRect(self):
        return QRectF(self.pixmap.rect())

    def paint(self, p, o, w=None):
        p.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, e):
        (
            self.clicked.emit()
            if e.button() == Qt.MouseButton.LeftButton
            else None
        )
        (
            e.accept()
            if e.button() == Qt.MouseButton.LeftButton
            else super().mousePressEvent(e)
        )


class AutoFitGraphicsView(QGraphicsView):
    def __init__(self, s, p=None):
        super().__init__(s, p)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMouseTracking(True)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self.scene() and not self.sceneRect().isEmpty():
            mw = self.window()
            # Wir nutzen hasattr, um Runtime-Fehler zu vermeiden, falls window() noch nicht fertig ist
            if (
                mw
                and hasattr(mw, "is_q1_maximized")
                and mw.is_q1_maximized
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


class RouteEditorScene(QGraphicsScene):
    clicked_point = pyqtSignal(QPointF)
    waiting_area_created = pyqtSignal(QRectF)

    def __init__(self, p=None):
        super().__init__(p)
        self.main_window = None  # Referenz wird in MainWindow.__init__ gesetzt
        self.rect_start = None
        self.temp_rect = None

    def mousePressEvent(self, e):
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
        if self.main_window.is_drawing_waiting_area and self.rect_start:
            self.waiting_area_created.emit(
                QRectF(self.rect_start, e.scenePos()).normalized()
            )
            self.removeItem(self.temp_rect)
            self.rect_start = None
            e.accept()
            return
        super().mouseReleaseEvent(e)
