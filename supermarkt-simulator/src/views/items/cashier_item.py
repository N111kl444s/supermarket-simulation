"""
Cashier item visualization.
Refactored:
- Uses DETERMINISTIC skin selection based on 'variant_index'.
- Prevents cashiers from changing appearance on every redraw.
- Loads random variants for 'Azubi' and 'Festangestellter' from configured lists.
"""

from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsPathItem, QGraphicsItemGroup
from PyQt6.QtCore import Qt, QRect, QPointF
from PyQt6.QtGui import QPixmap, QTransform, QPainter, QColor, QBrush, QPen, QPainterPath

from config import *
from PyQt6.QtGui import QPixmap, QTransform, QPainter, QColor, QBrush, QPen

class CashierItem(QGraphicsPixmapItem):
    # Class attributes
    _pixmaps_azubi = []
    _pixmaps_pro = []
    _images_loaded = False

    def __init__(self, x, y, skill, size=CASHIER_SIZE, variant_index=0):
        super().__init__()
        self._load_images()

        self.skill = str(skill).strip()
        self.size = size
        self.variant_index = variant_index
        self.cashier_id = variant_index  # Use variant_index as unique id for debugging/identification
        self.icon_name = None  # No icon by default

        # Initiale Zuweisung
        self.update_skill(self.skill)

        self.center_x = x
        self.center_y = y
        self._apply_position()

        self.setZValue(30)  # Cashier above screen, below ID
        self.setAcceptHoverEvents(True)

    def update_skill(self, new_skill):
        """Updates the image based on the new skill level."""
        self.skill = str(new_skill).strip()

        pool = []
        if self.skill == "Azubi":
            pool = self._pixmaps_azubi
        elif self.skill == "Festangestellter":
            pool = self._pixmaps_pro

        if pool:
            # Deterministische Auswahl: Immer das gleiche Bild für diesen Index
            idx = self.variant_index % len(pool)
            target_pixmap = pool[idx]
            self.setPixmap(target_pixmap)
        else:
            # Fallback Zeichnung
            fallback_col = (
                QColor("orange")
                if self.skill == "Festangestellter"
                else QColor("gray")
            )
            self.setPixmap(
                self._create_fallback_pixmap(
                    self.size, fallback_col, self.skill[0]
                )
            )

        self._apply_scaling()
        self._apply_position()

    def set_repairing(self, is_repairing, icon_name="tool.png"):
        """DEPRECATED: Repair visualization moved to checkout screen."""
        pass

    def set_repair_progress(self, progress: float):
        """DEPRECATED: Progress visualization moved to checkout screen."""
        pass

    def hoverEnterEvent(self, e):
        self.setToolTip(f"Mitarbeiter: {self.skill}")
        super().hoverEnterEvent(e)

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return

        # Lade Azubi Bilder
        for name in IMG_CASHIERS_AZUBI:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_azubi.append(QPixmap(str(p)))

        # Lade Festangestellter Bilder
        for name in IMG_CASHIERS_PRO:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_pro.append(QPixmap(str(p)))

        cls._images_loaded = True

    def _apply_position(self):
        if hasattr(self, "center_x") and hasattr(self, "center_y"):
            self.setPos(
                self.center_x - (self.size / 2),
                self.center_y - (self.size / 2),
            )

    def _apply_scaling(self):
        if self.pixmap().isNull():
            return
        orig_size = self.pixmap().size()
        if orig_size.width() > 0 and orig_size.height() > 0:
            scale_x = self.size / orig_size.width()
            scale_y = self.size / orig_size.height()
            self.setTransform(QTransform().scale(scale_x, scale_y))

    def _create_fallback_pixmap(self, size, color, letter):
        pix = QPixmap(int(size), int(size))
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawEllipse(1, 1, int(size) - 2, int(size) - 2)

        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(
            QRect(0, 0, int(size), int(size)),
            Qt.AlignmentFlag.AlignCenter,
            letter,
        )
        painter.end()
        return pix

