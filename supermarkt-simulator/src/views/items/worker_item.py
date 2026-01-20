"""
Visual representation of the maintenance worker.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItemGroup
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import Qt
from config import IMG_WORKER, ICON_TOOL
import math

class WorkerItem(QGraphicsItemGroup):
    def __init__(self, model, size=32):
        super().__init__()
        self.model = model
        self.target_size = size
        self.setZValue(25) # Über Kunden

        # Visuals
        self.worker_pix = QGraphicsPixmapItem()
        self.tool_pix = QGraphicsPixmapItem()
        
        self._load_images()
        self.addToGroup(self.worker_pix)
        self.addToGroup(self.tool_pix)
        
        self.tool_anim_angle = 0.0
        self.sync_visuals()

    def _load_images(self):
        if IMG_WORKER.exists():
            pix = QPixmap(str(IMG_WORKER))
            self.worker_pix.setPixmap(pix)
            # Scale Worker
            if pix.width() > 0:
                s = self.target_size / pix.width()
                self.worker_pix.setScale(s)
                self.worker_pix.setOffset(-pix.width()/2, -pix.height()/2)
                
        if ICON_TOOL.exists():
            pix = QPixmap(str(ICON_TOOL))
            self.tool_pix.setPixmap(pix)
            self.tool_pix.setScale(0.5) # Kleiner
            self.tool_pix.setOffset(-pix.width()/2, -pix.height()/2)
            self.tool_pix.setVisible(False)

    def sync_visuals(self):
        self.setPos(self.model.pos)
        
        # Werkzeug nur anzeigen wenn er arbeitet
        is_working = (self.model.state == "WORKING")
        self.tool_pix.setVisible(is_working)
        
        if is_working:
            # Animation: Werkzeug wackeln
            self.tool_anim_angle += 15
            self.tool_pix.setRotation(math.sin(math.radians(self.tool_anim_angle)) * 30)
            # Position über dem Kopf
            self.tool_pix.setPos(0, -20)
        else:
            self.tool_pix.setRotation(0)