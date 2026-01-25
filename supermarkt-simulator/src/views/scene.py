"""
Simulation Scene.
Refactored:
- FIX: TypeError in itemAt (removed keyword argument).
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

    def mousePressEvent(self, event):
        # Basis-Handling (Items selektieren etc.)
        super().mousePressEvent(event)

        # Linksklick auf leere Fläche -> Signal senden (für Regale/Kassen platzieren)
        if event.button() == Qt.MouseButton.LeftButton:
            views = self.views()
            item = None

            # FIX: itemAt darf keine Keyword-Arguments wie 'transform=' haben in manchen Bindings
            if views:
                # Wir nehmen die Transform-Matrix der ersten View
                transform = views[0].transform()
                item = self.itemAt(event.scenePos(), transform)
            else:
                # Fallback ohne Transform (weniger präzise bei Zoom, aber sicher)
                # Alternative: self.items(pos)[0]
                items_at_pos = self.items(event.scenePos())
                if items_at_pos:
                    item = items_at_pos[0]

            if not item:
                self.clicked_point.emit(event.scenePos())
            else:
                # Auch wenn Item da ist, leiten wir das Event weiter an den InteractionController,
                # der entscheidet dann (z.B. wenn man im Regal-Platzieren-Modus ist, ignoriert er Klicks auf andere Items)
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
