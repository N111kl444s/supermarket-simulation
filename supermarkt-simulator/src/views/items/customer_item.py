"""
Visual representation of a customer.
Refactored: 
- HD Rendering support.
- Correctly handles Normal vs. Disabled customer images.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QTransform
from config import *
import random

class CustomerItem(QGraphicsPixmapItem):
    _pixmaps_normal = []
    _pixmaps_disabled = []
    _images_loaded = False

    def __init__(self, model, size=32):
        super().__init__()
        self.model = model
        self.target_size = size
        self.setZValue(20) # Höher als Regale
        
        self._load_images()
        self.set_visuals()
        self.sync_visuals()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded: return
        
        # Load Normal
        for name in IMG_CUSTOMERS_NORMAL:
            path = IMAGE_DIR / name
            if path.exists():
                cls._pixmaps_normal.append(QPixmap(str(path)))
        
        # Load Disabled
        for name in IMG_CUSTOMERS_DISABLED:
            path = IMAGE_DIR / name
            if path.exists():
                cls._pixmaps_disabled.append(QPixmap(str(path)))
                
        cls._images_loaded = True

    def set_visuals(self):
        # Wähle passenden Pool
        pool = self._pixmaps_disabled if self.model.is_disabled else self._pixmaps_normal
        
        # Fallback auf Normal, falls Disabled leer
        if not pool and self.model.is_disabled:
            pool = self._pixmaps_normal
            
        if not pool: return
        
        raw_pixmap = random.choice(pool)
        self.setPixmap(raw_pixmap)
        
        # Scale Item down to target size (HD Rendering)
        if raw_pixmap.width() > 0:
            scale = self.target_size / raw_pixmap.width()
            self.setScale(scale)
            
        # Offset (in Original-Pixeln) damit Drehung um Mitte erfolgt
        w = raw_pixmap.width()
        h = raw_pixmap.height()
        self.setOffset(-w/2, -h/2)

    def sync_visuals(self):
        self.setPos(self.model.pos)
        self.setRotation(self.model.angle)