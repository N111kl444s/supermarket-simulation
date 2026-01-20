"""
Visual representation of a cashier.
Refactored:
- Supports random image variations for 'Azubi' and 'Festangestellt'.
- Loads images dynamically from config lists.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtGui import QPixmap, QTransform
from config import *
import random

class CashierItem(QGraphicsPixmapItem):
    _pixmaps_newbie = []
    _pixmaps_pro = []
    _images_loaded = False

    def __init__(self, data, size=32):
        super().__init__()
        self.data = data
        self.target_size = size
        self.setZValue(15)  # Etwas über dem Boden/Kasse

        self._load_images()
        self.set_visuals()
        
        # Position direkt setzen (aus Daten)
        self.setPos(data.get("x", 0), data.get("y", 0))

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return

        # Azubi Bilder laden
        for name in IMG_CASHIER_NEWBIE:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_newbie.append(QPixmap(str(p)))

        # Profi Bilder laden
        for name in IMG_CASHIER_PRO:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_pro.append(QPixmap(str(p)))

        cls._images_loaded = True

    def set_visuals(self):
        skill = self.data.get("skill", "Azubi")
        
        pool = []
        if skill == "Festangestellt":
            pool = self._pixmaps_pro
        else:
            # Fallback auf Azubi
            pool = self._pixmaps_newbie
            
        if not pool:
            # Sicherheits-Fallback falls Listen leer sind
            pool = self._pixmaps_newbie

        if not pool:
            return

        # Zufälliges Bild aus dem Pool wählen
        raw_pixmap = random.choice(pool)
        self.setPixmap(raw_pixmap)

        # Skalieren und Zentrieren
        if raw_pixmap.width() > 0:
            scale = self.target_size / raw_pixmap.width()
            self.setScale(scale)
            
            # Offset setzen, damit (0,0) die Mitte ist
            w = raw_pixmap.width()
            h = raw_pixmap.height()
            self.setOffset(-w / 2, -h / 2)