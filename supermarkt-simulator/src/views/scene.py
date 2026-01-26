"""
Simulation Scene.
Refactored:
- FIX: No circular imports.
- LOGIC: Handles temporary drawing of selection rectangles.
"""

from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush


class SimulationScene(QGraphicsScene):
    # Signale für Interaktion
    clicked_point = pyqtSignal(QPointF)
    waiting_area_created = pyqtSignal(QRectF)  # Wird für ALLE Areas genutzt

    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_rect_item = None
        self.start_point = None

        # Hintergrund-Gitter oder ähnliches könnte man hier initen
        # self.setBackgroundBrush(QBrush(QColor("#F5F7FA")))

    def mousePressEvent(self, event):
        # Basis-Handling (Items selektieren etc.)
        super().mousePressEvent(event)

        # Linksklick auf leere Fläche -> Signal senden (für Regale/Kassen platzieren)
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.itemAt(
                event.scenePos(), self.views()[0].transform()
            ):
                self.clicked_point.emit(event.scenePos())
            else:
                # Auch wenn Item da ist, wollen wir das Event für Logic nutzen (z.B. Kasse anklicken)
                # Aber VisualController handled Klicks auf Items direkt via Item-Callbacks.
                # Wir senden clicked_point trotzdem für Map-Move oder Placement-Logic.
                self.clicked_point.emit(event.scenePos())

    def start_drawing_area(self, pos):
        """Startet das Zeichnen eines Rechtecks."""
        self.start_point = pos
        self.temp_rect_item = QGraphicsRectItem()
        self.temp_rect_item.setPen(
            QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine)
        )
        self.temp_rect_item.setBrush(
            QBrush(QColor(0, 0, 0, 30))
        )  # Leicht transparentes Grau
        self.addItem(self.temp_rect_item)
        self.temp_rect_item.setRect(QRectF(pos, pos))

    def update_drawing_area(self, pos):
        """Aktualisiert das Rechteck während der Mausbewegung."""
        if self.temp_rect_item and self.start_point:
            rect = QRectF(self.start_point, pos).normalized()
            self.temp_rect_item.setRect(rect)

    def finish_drawing_area(self):
        """Beendet das Zeichnen und sendet das Rechteck."""
        if self.temp_rect_item:
            final_rect = self.temp_rect_item.rect()

            # Aufräumen
            self.removeItem(self.temp_rect_item)
            self.temp_rect_item = None
            self.start_point = None

            # Nur senden wenn Größe > 0
            if final_rect.width() > 5 and final_rect.height() > 5:
                self.waiting_area_created.emit(final_rect)
