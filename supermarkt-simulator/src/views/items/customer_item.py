"""
Visual representation of a customer.
Refactored: 
- HD Rendering support.
- Static movement (No rotation).
- Correctly handles Normal vs. Disabled customer images.
- Added: Item Count Label above head (Hübscher und kleiner).
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsSimpleTextItem
from PyQt6.QtGui import QPixmap, QTransform, QFont, QColor, QBrush, QPen
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
        
        # Label ZUERST erstellen
        self._create_label()
        
        self.current_scale = 1.0
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

    def _create_label(self):
        """Erstellt die Anzeige für die Artikelanzahl."""
        self.label = QGraphicsSimpleTextItem("0", self)
        
        # Schriftart (kleiner: 8 statt 10)
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        self.label.setFont(font)
        
        # Farbe: Weißer Text mit schwarzer Umrandung (Outline) für Kontrast
        self.label.setBrush(QBrush(QColor("white")))
        # Etwas dickerer Rand (1 statt 0) für bessere Lesbarkeit bei kleiner Größe
        self.label.setPen(QPen(QColor("black"), 1)) 
        
        self.label.setZValue(100) # Ganz oben

    def set_visuals(self):
        pool = self._pixmaps_disabled if self.model.is_disabled else self._pixmaps_normal
        if not pool and self.model.is_disabled:
            pool = self._pixmaps_normal
            
        if not pool: return
        
        raw_pixmap = random.choice(pool)
        self.setPixmap(raw_pixmap)
        
        # Skalierung berechnen
        if raw_pixmap.width() > 0:
            self.current_scale = self.target_size / raw_pixmap.width()
            self.setScale(self.current_scale)
        else:
            self.current_scale = 1.0
            
        w = raw_pixmap.width()
        h = raw_pixmap.height()
        self.setOffset(-w/2, -h/2)

    def sync_visuals(self):
        self.setPos(self.model.pos)
        # Keine Rotation
        
        # --- LABEL UPDATE ---
        count_str = str(self.model.item_count)
        if self.label.text() != count_str:
            self.label.setText(count_str)
            
        # --- LABEL POS & SCALE ---
        # Inverse Skalierung damit das Label lesbar bleibt
        if self.current_scale > 0.0001:
            inv_scale = 1.0 / self.current_scale
            # Wir machen es etwas kleiner relativ zur Szene (Faktor 0.7 statt 1.0)
            desired_label_scale = inv_scale * 0.7
            
            br = self.label.boundingRect()
            
            # Transform:
            # 1. Zum Kopf des Kunden bewegen (top center of image): (0, -height/2)
            # 2. Skalieren
            # 3. Text zentrieren (bottom center of text to anchor)
            
            t = QTransform()
            t.translate(0, -self.pixmap().height() / 2) # Anker am Kopf
            t.scale(desired_label_scale, desired_label_scale) # Groß skalieren
            # Etwas mehr Abstand nach oben (+2 units im scaled space)
            t.translate(-br.width() / 2, -br.height() - 2) 
            
            self.label.setTransform(t)