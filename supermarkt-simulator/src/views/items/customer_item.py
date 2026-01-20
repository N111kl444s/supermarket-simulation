"""
Visual representation of a customer.
Refactored:
- HD Rendering support.
- Static movement (No rotation).
- Correctly handles Normal vs. Disabled customer images.
- UPDATED: Info Box layout:
  - Top: Small Payment Method Icon
  - Center: Item Count (replaced by Large Payment Icon during 'PAYING' state)
  - Bottom: Handheld Icon (if applicable)
- NEW: Scan Animation (Background fills green from top to bottom).
- NEW: Payment Animation (Background fills green slowly based on payment duration).
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
    _cash_icon = None
    _card_icon = None
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
        self.pulse_val = 0.0         # 1.0 -> 0.0 (Green Flash beim Aufheben)
        self.clock_progress = 0.0    # 0.0 -> 1.0 (Scan Fortschritt)
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
        
        # Scanner
        if ICON_SCANNER.exists():
            cls._scanner_icon = QPixmap(str(ICON_SCANNER))
        else:
            cls._scanner_icon = QPixmap()
            
        # Cash
        if ICON_CASH.exists():
            cls._cash_icon = QPixmap(str(ICON_CASH))
        else:
            cls._cash_icon = QPixmap() # Fallback empty
            
        # Card
        if ICON_CARD.exists():
            cls._card_icon = QPixmap(str(ICON_CARD))
        else:
            cls._card_icon = QPixmap()

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

        # 1b. Scan/Pay Animation (Fill Overlay)
        self.scan_fill = QGraphicsPathItem()
        self.scan_fill.setBrush(QBrush(QColor(144, 238, 144))) 
        self.scan_fill.setPen(QPen(Qt.PenStyle.NoPen))
        self.info_group.addToGroup(self.scan_fill)

        # 2. Payment Icon (Top Small / Big Center)
        self.payment_icon_item = QGraphicsPixmapItem()
        self.info_group.addToGroup(self.payment_icon_item)

        # 3. Scanner/Handheld Icon (Bottom)
        self.handheld_icon_item = QGraphicsPixmapItem()
        if self._scanner_icon and not self._scanner_icon.isNull():
            self.handheld_icon_item.setPixmap(self._scanner_icon)
        self.info_group.addToGroup(self.handheld_icon_item)

        # 4. Text (Artikelanzahl)
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

        # --- BOX INHALT & LAYOUT ---
        is_paying = (self.model.state == "PAYING")
        
        # Text update
        count_str = str(current_count)
        if self.text_item.text() != count_str:
            self.text_item.setText(count_str)
        
        # Payment Icon bestimmen
        use_card = (self.model.payment_method == 'card')
        pay_pix = self._card_icon if use_card else self._cash_icon
        
        # Handheld check
        has_handheld = (
            self.model.uses_handheld
            and self._scanner_icon
            and not self._scanner_icon.isNull()
        )

        # --- VISIBILITY & SCALING ---
        
        # 1. Text Visibility: Nur sichtbar wenn NICHT bezahlt wird
        self.text_item.setVisible(not is_paying)
        
        # 2. Payment Icon Setup
        if pay_pix and not pay_pix.isNull():
            self.payment_icon_item.setPixmap(pay_pix)
            self.payment_icon_item.setVisible(True)
        else:
            self.payment_icon_item.setVisible(False)

        # 3. Handheld Visibility
        self.handheld_icon_item.setVisible(has_handheld)

        # --- LAYOUT CALCULATION ---
        
        padding = 2
        spacing = 1
        
        # Base Text Dimensions
        txt_rect = self.text_item.boundingRect()
        txt_h = txt_rect.height()
        
        # Icon Dimensions (Reference Height based on Text)
        ref_h = txt_h * 0.8
        
        # Payment Icon Scale & Size
        pay_w, pay_h = 0, 0
        if self.payment_icon_item.isVisible():
            if is_paying:
                # Big Icon (replaces text)
                target_pay_h = txt_h * 1.5 
            else:
                # Small Icon (top)
                target_pay_h = txt_h * 0.6
                
            if pay_pix.height() > 0:
                scale_pay = target_pay_h / pay_pix.height()
                self.payment_icon_item.setScale(scale_pay)
                pay_w = pay_pix.width() * scale_pay
                pay_h = target_pay_h

        # Handheld Icon Scale & Size
        hand_w, hand_h = 0, 0
        if has_handheld:
            scale_hand = ref_h / self._scanner_icon.height()
            self.handheld_icon_item.setScale(scale_hand)
            hand_w = self._scanner_icon.width() * scale_hand
            hand_h = ref_h

        # Total Dimensions
        # Stack: [Payment] -> [Text OR BigPayment] -> [Handheld]
        
        row1_h = 0 # Small Payment (if not paying)
        row2_h = 0 # Center (Text or Big Payment)
        row3_h = 0 # Handheld
        
        max_w = 0
        
        if is_paying:
            # Row 2 ist das große Icon
            row2_h = pay_h
            max_w = max(max_w, pay_w)
        else:
            # Row 1: Small Payment Icon
            if self.payment_icon_item.isVisible():
                row1_h = pay_h
                max_w = max(max_w, pay_w)
            
            # Row 2: Text
            row2_h = txt_h
            max_w = max(max_w, txt_rect.width())
            
        if has_handheld:
            row3_h = hand_h
            max_w = max(max_w, hand_w)
            
        total_h = row1_h + row2_h + row3_h + (padding * 2)
        if row1_h > 0: total_h += spacing
        if row3_h > 0: total_h += spacing
        
        total_w = max_w + (padding * 4) # Etwas breiter für Look

        # --- POSITIONING ---
        curr_y = padding
        
        # 1. Row 1 (Small Payment)
        if not is_paying and row1_h > 0:
            self.payment_icon_item.setPos((total_w - pay_w) / 2, curr_y)
            curr_y += row1_h + spacing
            
        # 2. Row 2 (Center Content)
        if is_paying:
            # Big Payment Icon
            self.payment_icon_item.setPos((total_w - pay_w) / 2, curr_y)
            curr_y += row2_h + spacing
        else:
            # Text
            self.text_item.setPos((total_w - txt_rect.width()) / 2, curr_y)
            curr_y += row2_h + spacing

        # 3. Row 3 (Handheld)
        if has_handheld:
            self.handheld_icon_item.setPos((total_w - hand_w) / 2, curr_y)
            
        # --- BACKGROUND & TRANSFORM ---
        base_path = QPainterPath()
        base_path.addRoundedRect(0, 0, total_w, total_h, 3, 3)
        self.box_bg.setPath(base_path)

        if self.current_scale > 0.0001:
            k = (self.target_size * 0.45) / (total_h * self.current_scale)
            t = QTransform()
            t.translate(0, -self.pixmap().height() / 2)
            t.scale(k, k)
            t.translate(-total_w / 2, -total_h * 1.5)
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

        # 2. Fill Animation (Zustand: BEZAHLEN oder SCANNEN)
        
        fill_progress = 0.0
        should_render_fill = False

        if is_paying and self.model.payment_duration > 0:
            # NEU: Langsame Füll-Animation während des Bezahlens
            # Berechne Fortschritt basierend auf Timer
            fill_progress = min(1.0, self.model.payment_timer / self.model.payment_duration)
            should_render_fill = True
            
            # Falls noch eine alte Scan-Animation läuft, abbrechen
            self.is_clock_animating = False

        elif self.is_clock_animating:
            # Schnelle Scan-Animation
            self.clock_progress += 0.40
            if self.clock_progress >= 1.0:
                self.clock_progress = 1.0
                self.is_clock_animating = False
                # Hier nicht rendern, sondern resetten im 'else' Zweig beim nächsten Tick
                # aber für diesen Frame zeichnen wir noch voll
            
            fill_progress = self.clock_progress
            should_render_fill = True

        if should_render_fill:
            fill_height = total_h * fill_progress
            fill_rect_path = QPainterPath()
            fill_rect_path.addRect(0, 0, total_w, fill_height)
            final_path = base_path.intersected(fill_rect_path)
            self.scan_fill.setPath(final_path)
        else:
            if not self.scan_fill.path().isEmpty():
                self.scan_fill.setPath(QPainterPath())