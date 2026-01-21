"""
Worker (Technician) Graphics Item.
Shows the worker and a tool icon when repairing.
"""

from PyQt6.QtWidgets import QGraphicsObject
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor
from config import IMAGE_DIR, CUSTOMER_SIZE  # Reuse size or define new


class WorkerItem(QGraphicsObject):
    _pixmaps = {}
    _loaded = False

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.width = CUSTOMER_SIZE
        self.height = CUSTOMER_SIZE
        self._load_resources()

        self.setZValue(15)  # Über Kunden

    @classmethod
    def _load_resources(cls):
        if cls._loaded:
            return
        # Wir nutzen worker.png und tool.png
        # Falls nicht vorhanden, Fallback
        p_worker = IMAGE_DIR / "worker.png"
        p_tool = IMAGE_DIR / "tool.png"

        if p_worker.exists():
            cls._pixmaps["worker"] = QPixmap(str(p_worker))
        if p_tool.exists():
            cls._pixmaps["tool"] = QPixmap(str(p_tool))

        cls._loaded = True

    def boundingRect(self):
        return QRectF(
            -self.width / 2, -self.height / 2, self.width, self.height
        )

    def paint(self, painter: QPainter, option, widget=None):
        pix = self._pixmaps.get("worker")
        rect = self.boundingRect()

        # Worker Body
        if pix:
            painter.drawPixmap(rect.toRect(), pix)
        else:
            painter.setBrush(QColor("orange"))
            painter.drawEllipse(rect)

        # Tool Animation
        if self.model.is_fixing:
            tool_pix = self._pixmaps.get("tool")
            if tool_pix:
                # Tool über dem Kopf zeichnen
                tool_rect = QRectF(-10, -self.height, 20, 20)
                painter.drawPixmap(tool_rect.toRect(), tool_pix)
            else:
                # Fallback blinkender Kreis
                painter.setBrush(QColor("red"))
                painter.drawEllipse(QRectF(-5, -self.height, 10, 10))

    def update_visuals(self, dt):
        self.setPos(self.model.pos)
        # Rotation
        # Wir drehen das Bild nicht unbedingt, aber wir könnten (self.setRotation(self.model.angle))
        # Da Sprites meist von oben sind:
        # self.setRotation(self.model.angle)
        self.update()
