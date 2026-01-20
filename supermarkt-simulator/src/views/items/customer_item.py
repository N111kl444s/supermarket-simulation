"""
Visual representation of a customer.
Refactored:
- HD Rendering support.
- Static movement (No rotation).
- Correctly handles Normal vs. Disabled customer images.
- UPDATED: Info Box smaller & compact layout (Number top, Icon bottom).
- NEW: Scan Animation (Background fills green from top to bottom).
- FIX: Animation speed increased to prevent "incomplete" look on fast scans.
"""

from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsSimpleTextItem,
    QGraphicsItemGroup,
    QGraphicsPathItem,
)
from PyQt6.QtGui import (
    QPixmap,
    QTransform,
    QFont,
    QColor,
    QBrush,
    QPen,
    QPainterPath,
)
from PyQt6.QtCore import Qt, QRectF
from config import *
import random


class CustomerItem(QGraphicsPixmapItem):
    _pixmaps_normal = []
    _pixmaps_disabled = []
    _pixmaps_handheld = []
    _pixmaps_handheld_disabled = []

    _scanner_icon = None
    _images_loaded = False

    def __init__(self, model, size=32):
        super().__init__()
        self.model = model
        self.target_size = size
        self.setZValue(20)  # Höher als Regale

        self._load_images()
        self._load_icons()

        # Animation State
        self._last_item_count = self.model.item_count
        self.pulse_val = 0.0  # 1.0 -> 0.0 (Green Flash beim Aufheben)
        self.clock_progress = 0.0  # 0.0 -> 1.0 (Scan Fortschritt)
        self.is_clock_animating = False

        # Info Box erstellen
        self._create_info_box()

        self.current_scale = 1.0
        self.set_visuals()
        self.sync_visuals()

    @classmethod
    def _load_images(cls):
        if cls._images_loaded:
            return

        for name in IMG_CUSTOMERS_NORMAL:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_normal.append(QPixmap(str(p)))

        for name in IMG_CUSTOMERS_DISABLED:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_disabled.append(QPixmap(str(p)))

        for name in IMG_CUSTOMERS_HANDHELD:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_handheld.append(QPixmap(str(p)))

        for name in IMG_CUSTOMERS_HANDHELD_DISABLED:
            p = IMAGE_DIR / name
            if p.exists():
                cls._pixmaps_handheld_disabled.append(QPixmap(str(p)))

        cls._images_loaded = True

    @classmethod
    def _load_icons(cls):
        if cls._scanner_icon is not None:
            return
        icon_path = ASSETS_DIR / "icons" / "thermal-scanner.png"
        if icon_path.exists():
            cls._scanner_icon = QPixmap(str(icon_path))
        else:
            cls._scanner_icon = QPixmap()

    def _create_info_box(self):
        """Erstellt die moderne Info-Box Gruppe."""
        self.info_group = QGraphicsItemGroup(self)
        self.info_group.setZValue(100)

        # 1. Hintergrund Box
        self.box_bg = QGraphicsPathItem()
        self.box_bg.setBrush(QBrush(QColor(255, 255, 255, 230)))
        self.default_pen = QPen(QColor(80, 80, 80), 0.5)
        self.box_bg.setPen(self.default_pen)
        self.info_group.addToGroup(self.box_bg)

        # 1b. Scan Animation (Fill Overlay)
        # Liegt über dem Hintergrund, aber unter dem Text/Icon.
        self.scan_fill = QGraphicsPathItem()
        # Helles Grün, damit schwarzer Text lesbar bleibt
        self.scan_fill.setBrush(QBrush(QColor(144, 238, 144)))
        self.scan_fill.setPen(QPen(Qt.PenStyle.NoPen))
        self.info_group.addToGroup(self.scan_fill)

        # 2. Scanner Icon
        self.icon_item = QGraphicsPixmapItem()
        if self._scanner_icon and not self._scanner_icon.isNull():
            self.icon_item.setPixmap(self._scanner_icon)
        self.info_group.addToGroup(self.icon_item)

        # 3. Text (Artikelanzahl)
        self.text_item = QGraphicsSimpleTextItem("0")
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        self.text_item.setFont(font)
        self.text_item.setBrush(QBrush(QColor("black")))
        self.info_group.addToGroup(self.text_item)

    def set_visuals(self):
        pool = []
        if self.model.uses_handheld:
            if self.model.is_disabled:
                pool = (
                    self._pixmaps_handheld_disabled or self._pixmaps_disabled
                )
            else:
                pool = self._pixmaps_handheld or self._pixmaps_normal
        elif self.model.is_disabled:
            pool = self._pixmaps_disabled
        else:
            pool = self._pixmaps_normal

        if not pool:
            pool = self._pixmaps_normal
        if not pool:
            return

        raw_pixmap = random.choice(pool)
        self.setPixmap(raw_pixmap)

        if raw_pixmap.width() > 0:
            self.current_scale = self.target_size / raw_pixmap.width()
            self.setScale(self.current_scale)
        else:
            self.current_scale = 1.0

        w = raw_pixmap.width()
        h = raw_pixmap.height()
        self.setOffset(-w / 2, -h / 2)

    def sync_visuals(self):
        self.setPos(self.model.pos)

        # --- LOGIC TRIGGER DETECTION ---
        current_count = self.model.item_count

        # 1. Pulse (Regal): Wenn Item-Count steigt
        if current_count > self._last_item_count:
            self.pulse_val = 1.0

        # 2. Scan Trigger (Kasse)
        if self.model.trigger_scan_anim:
            self.is_clock_animating = True
            self.clock_progress = 0.0

        self._last_item_count = current_count

        # --- BOX INHALT & LAYOUT (Zuerst, damit wir die Maße für Animation haben) ---
        count_str = str(current_count)
        if self.text_item.text() != count_str:
            self.text_item.setText(count_str)

        has_handheld = (
            self.model.uses_handheld
            and self._scanner_icon
            and not self._scanner_icon.isNull()
        )

        padding_x = 3
        padding_y = 1
        spacing_y = 0
        txt_rect = self.text_item.boundingRect()
        txt_w = txt_rect.width()
        txt_h = txt_rect.height()
        icon_w = 0
        icon_h = 0

        if has_handheld:
            self.icon_item.setVisible(True)
            target_icon_h = txt_h * 0.8
            scale_icon = target_icon_h / self._scanner_icon.height()
            self.icon_item.setScale(scale_icon)
            icon_w = self._scanner_icon.width() * scale_icon
            icon_h = target_icon_h
        else:
            self.icon_item.setVisible(False)

        content_w = max(txt_w, icon_w)
        content_h = txt_h
        if has_handheld:
            content_h += spacing_y + icon_h

        box_w = padding_x * 2 + content_w
        box_h = padding_y * 2 + content_h

        # Hintergrund-Pfad setzen (Abgerundetes Rechteck)
        base_path = QPainterPath()
        base_path.addRoundedRect(0, 0, box_w, box_h, 3, 3)
        self.box_bg.setPath(base_path)

        curr_y = padding_y
        self.text_item.setPos((box_w - txt_w) / 2, curr_y)
        curr_y += txt_h + spacing_y
        if has_handheld:
            self.icon_item.setPos((box_w - icon_w) / 2, curr_y)

        # Gruppe transformieren
        if self.current_scale > 0.0001:
            k = (self.target_size * 0.35) / (box_h * self.current_scale)
            t = QTransform()
            t.translate(0, -self.pixmap().height() / 2)
            t.scale(k, k)
            t.translate(-box_w / 2, -box_h * 1.5)
            self.info_group.setTransform(t)

        # --- ANIMATION RENDERING ---

        # 1. Pulse Animation (Regal - Aufheben)
        if self.pulse_val > 0:
            self.pulse_val -= 0.1
            if self.pulse_val < 0:
                self.pulse_val = 0

            # Farbe interpolieren (Grau -> Grün)
            val = int(255 * self.pulse_val)
            inv = int(80 * (1.0 - self.pulse_val))
            color = QColor(inv, val + inv, inv)
            width = 0.5 + (2.0 * self.pulse_val)
            self.box_bg.setPen(QPen(color, width))
        else:
            if self.box_bg.pen() != self.default_pen:
                self.box_bg.setPen(self.default_pen)

        # 2. Fill Animation (Kasse - Scan Top-Down)
        if self.is_clock_animating:
            # FIX: Geschwindigkeit deutlich erhöht (0.15 -> 0.40),
            # damit die Animation auch bei schnellen Scans fertig wird.
            self.clock_progress += 0.40
            if self.clock_progress >= 1.0:
                self.clock_progress = 1.0
                self.is_clock_animating = False
                self.scan_fill.setPath(QPainterPath())  # Reset
            else:
                # Füll-Rechteck berechnen (0 bis box_h)
                fill_height = box_h * self.clock_progress

                fill_rect_path = QPainterPath()
                fill_rect_path.addRect(0, 0, box_w, fill_height)

                # Wir schneiden das Füll-Rechteck mit der abgerundeten Hintergrund-Form.
                # So bleibt die Füllung innerhalb der runden Ecken.
                final_path = base_path.intersected(fill_rect_path)

                self.scan_fill.setPath(final_path)
        else:
            if not self.scan_fill.path().isEmpty():
                self.scan_fill.setPath(QPainterPath())
