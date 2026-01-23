"""
Worker Graphics Item.
Displays the maintenance worker and the tool icon during repair.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import Qt, QPointF
from config import IMG_WORKER, IMG_TOOL, IMAGE_DIR, ICON_DIR


class WorkerItem(QGraphicsPixmapItem):
    def __init__(self, model, size=32):
        super().__init__()
        self.model = model
        self.size = size
        self.current_state = None

        # Worker Image Load
        img_name = IMG_WORKER[0] if IMG_WORKER else "worker.png"
        path = IMAGE_DIR / img_name
        if path.exists():
            original = QPixmap(str(path))
            self.setPixmap(
                original.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        # Center Pivot
        self.setTransformOriginPoint(size / 2, size / 2)

        # Tool Icon (Overlay)
        self.tool_item = QGraphicsPixmapItem(self)
        self._load_tool_image()
        self.tool_item.setVisible(False)
        self.tool_item.setZValue(10)  # Über dem Worker

        self.setZValue(50)  # Über Kunden (meistens)

    def _load_tool_image(self):
        # Versuche Icon Dir dann Image Dir
        p1 = ICON_DIR / IMG_TOOL
        p2 = IMAGE_DIR / IMG_TOOL
        path = p1 if p1.exists() else p2

        if path.exists():
            pix = QPixmap(str(path))
            # Tool etwas kleiner als Worker
            tsize = int(self.size * 0.8)
            self.tool_item.setPixmap(
                pix.scaled(
                    tsize,
                    tsize,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            # Positionieren über dem Kopf
            self.tool_item.setPos(self.size / 2 - tsize / 2, -tsize)

    def sync_visuals(self):
        """
        Updates position and overlays based on model state.
        """
        # Position
        self.setPos(
            self.model.pos.x() - self.size / 2,
            self.model.pos.y() - self.size / 2,
        )

        # Rotation (Gesicht in Laufrichtung)
        self.setRotation(self.model.rotation)

        # Tool Visibility
        if self.model.state == "REPAIRING":
            if not self.tool_item.isVisible():
                self.tool_item.setVisible(True)
                # Tool soll nicht mitrotieren, sondern gerade bleiben -> Counter Rotation
                self.tool_item.setRotation(-self.model.rotation)
        else:
            if self.tool_item.isVisible():
                self.tool_item.setVisible(False)
