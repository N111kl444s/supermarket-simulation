"""
Cashier item visualization.
Refactored: 
- Debug Prints for Image Loading
- Robust Skill String Matching
- Fallback visualization
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QTransform, QPainter, QColor, QBrush, QPen
from config import *


class CashierItem(QGraphicsPixmapItem):
    """
    Visual representation of a cashier employee using PNG sprites.
    """
    _pixmap_azubi = None
    _pixmap_pro = None
    _images_loaded = False

    def __init__(self, x, y, skill, size=CASHIER_SIZE):
        super().__init__()
        self._load_images()
        
        self.skill = skill
        self.size = size
        
        print(f"DEBUG: New CashierItem created at ({x},{y}). Skill='{skill}', Size={size}")
        
        # Initiale Zuweisung
        self.update_skill(skill)
        
        # Speichere Zentrum für spätere Updates
        self.center_x = x
        self.center_y = y
        self._apply_position()

        self.setZValue(25)
        self.setAcceptHoverEvents(True)

    def update_skill(self, new_skill):
        """Updates the image based on the new skill level."""
        self.skill = str(new_skill).strip() # Entferne Leerzeichen zur Sicherheit
        target_pixmap = None
        
        print(f"DEBUG: CashierItem update_skill -> '{self.skill}'")

        if self.skill == "Azubi":
            if self._pixmap_azubi and not self._pixmap_azubi.isNull():
                target_pixmap = self._pixmap_azubi
            else:
                print("DEBUG: Azubi gewählt, aber Bild ist null!")
                
        elif self.skill == "Festangestellter":
            if self._pixmap_pro and not self._pixmap_pro.isNull():
                target_pixmap = self._pixmap_pro
            else:
                print("DEBUG: Festangestellter gewählt, aber Bild ist null!")
        
        # WICHTIG: Wenn Bild gefunden, setzen.
        if target_pixmap:
            self.setPixmap(target_pixmap)
        else:
            # FIX: Fallback, wenn Bild fehlt oder Skill unbekannt
            print(f"DEBUG: Nutze Fallback für Skill '{self.skill}'")
            fallback_col = QColor("orange") if self.skill == "Festangestellter" else QColor("gray")
            self.setPixmap(self._create_fallback_pixmap(self.size, fallback_col, self.skill[0]))

        self._apply_scaling()
        self._apply_position()

    def _create_fallback_pixmap(self, size, color, letter):
        """Erzeugt ein temporäres Pixmap, falls das PNG fehlt."""
        pix = QPixmap(int(size), int(size))
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Kreis
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawEllipse(1, 1, int(size)-2, int(size)-2)
        
        # Buchstabe
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(QRect(0, 0, int(size), int(size)), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()
        return pix

    def _apply_scaling(self):
        if self.pixmap().isNull():
            return
            
        orig_size = self.pixmap().size()
        if orig_size.width() > 0 and orig_size.height() > 0:
            # Wir skalieren so, dass es in self.size passt
            scale_x = self.size / orig_size.width()
            scale_y = self.size / orig_size.height()
            self.setTransform(QTransform().scale(scale_x, scale_y))

    def _apply_position(self):
        if hasattr(self, 'center_x'):
            self.setPos(
                self.center_x - (self.size / 2), 
                self.center_y - (self.size / 2)
            )

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return
        
        print(f"DEBUG: Lade Kassierer-Bilder...")
        
        # Lade Azubi
        if PATH_AZUBI.exists():
            cls._pixmap_azubi = QPixmap(str(PATH_AZUBI))
            print(f"DEBUG: Azubi geladen: {PATH_AZUBI}")
        else:
            print(f"WARNUNG: Azubi-Bild NICHT gefunden unter {PATH_AZUBI}")

        # Lade Festangestellter
        if PATH_PRO.exists():
            cls._pixmap_pro = QPixmap(str(PATH_PRO))
            print(f"DEBUG: Festangestellter geladen: {PATH_PRO}")
        else:
            print(f"WARNUNG: Festangestellter-Bild NICHT gefunden unter {PATH_PRO}")
            
        cls._images_loaded = True

    def hoverEnterEvent(self, e):
        self.setToolTip(f"Mitarbeiter: {self.skill}")
        super().hoverEnterEvent(e)
