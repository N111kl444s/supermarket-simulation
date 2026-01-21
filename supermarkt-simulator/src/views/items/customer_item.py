"""
Visual representation of a customer.
Refactored:
- HD Rendering support.
- Static movement (No rotation).
- Correctly handles Normal vs. Disabled customer images.
- UPDATED: Info Box Layout to include Payment Method Icon (Cash/Card).
- Layout:
    Top: Payment Icon (Small)
    Middle: Item Count
    Bottom: Handheld Icon (Small)
- CHECKOUT ANIMATION: Replaces Count with Big Payment Icon during 'PAYING' state.
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

        # Scanner
        icon_path = ASSETS_DIR / "icons" / "thermal-scanner.png"
        if icon_path.exists():
            cls._scanner_icon = QPixmap(str(icon_path))
        else:
            cls._scanner_icon = QPixmap()

        # Cash
        cash_path = ASSETS_DIR / "icons" / "cash.png"
        if cash_path.exists():
            cls._cash_icon = QPixmap(str(cash_path))
        else:
            cls._cash_icon = QPixmap()

        # Card
        card_path = ASSETS_DIR / "icons" / "card.png"
        if card_path.exists():
            cls._card_icon = QPixmap(str(card_path))
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
        self.scan_fill.setBrush(QBrush(QColor(144, 238, 144)))  # Light Green
        self.scan_fill.setPen(QPen(Qt.PenStyle.NoPen))
        self.info_group.addToGroup(self.scan_fill)

        # 2. Icons
        self.icon_handheld = QGraphicsPixmapItem()
        if self._scanner_icon and not self._scanner_icon.isNull():
            self.icon_handheld.setPixmap(self._scanner_icon)
        self.info_group.addToGroup(self.icon_handheld)

        self.icon_payment = QGraphicsPixmapItem()
        # Vorab Pixmap laden je nach Model
        if (
            self.model.payment_method == "cash"
            and self._cash_icon
            and not self._cash_icon.isNull()
        ):
            self.icon_payment.setPixmap(self._cash_icon)
        elif (
            self.model.payment_method == "card"
            and self._card_icon
            and not self._card_icon.isNull()
        ):
            self.icon_payment.setPixmap(self._card_icon)
        self.info_group.addToGroup(self.icon_payment)

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

        current_count = self.model.item_count
        is_paying = self.model.state == "PAYING"

        # 1. Pulse Trigger
        if current_count > self._last_item_count:
            self.pulse_val = 1.0

        # 2. Animation Trigger
        if self.model.trigger_scan_anim:
            self.is_clock_animating = True
            self.clock_progress = 0.0

        self._last_item_count = current_count

        # --- LAYOUT LOGIC ---

        # Constants
        padding_x = 3
        padding_y = 2
        spacing_y = 1

        # 1. Elements
        # Text
        count_str = str(current_count)
        if self.text_item.text() != count_str:
            self.text_item.setText(count_str)
        txt_rect = self.text_item.boundingRect()
        txt_w, txt_h = txt_rect.width(), txt_rect.height()

        # Handheld Icon
        has_handheld = (
            self.model.uses_handheld
            and not self.icon_handheld.pixmap().isNull()
        )
        hh_w, hh_h = 0, 0
        if has_handheld:
            # Scale Handheld icon to fit roughly text height
            target_hh = txt_h * 0.8
            scale_hh = target_hh / self.icon_handheld.pixmap().height()
            self.icon_handheld.setScale(scale_hh)
            hh_w = self.icon_handheld.pixmap().width() * scale_hh
            hh_h = target_hh

        # Payment Icon
        has_payment = not self.icon_payment.pixmap().isNull()
        pay_w, pay_h = 0, 0

        if is_paying:
            # Large Icon Mode
            self.text_item.setVisible(False)
            self.icon_handheld.setVisible(
                False
            )  # Hide handheld during big payment anim? Or keep? Let's hide to focus
            self.icon_payment.setVisible(True)

            # Big Payment Icon
            target_big = txt_h * 2.0
            scale_pay = target_big / self.icon_payment.pixmap().height()
            self.icon_payment.setScale(scale_pay)
            pay_w = self.icon_payment.pixmap().width() * scale_pay
            pay_h = target_big

            content_w = pay_w
            content_h = pay_h

        else:
            # Normal Mode: Stack -> Pay (Small) | Text | Handheld (Small)
            self.text_item.setVisible(True)
            self.icon_handheld.setVisible(has_handheld)
            self.icon_payment.setVisible(has_payment)

            if has_payment:
                target_small = txt_h * 0.8
                scale_pay = target_small / self.icon_payment.pixmap().height()
                self.icon_payment.setScale(scale_pay)
                pay_w = self.icon_payment.pixmap().width() * scale_pay
                pay_h = target_small

            # Max width of the column
            content_w = max(txt_w, hh_w, pay_w)

            # Total height calculation
            content_h = txt_h
            if has_payment:
                content_h += spacing_y + pay_h
            if has_handheld:
                content_h += spacing_y + hh_h

        # 2. Box Dimensions
        box_w = padding_x * 2 + content_w
        box_h = padding_y * 2 + content_h

        # 3. Positioning
        base_path = QPainterPath()
        base_path.addRoundedRect(0, 0, box_w, box_h, 3, 3)
        self.box_bg.setPath(base_path)

        curr_y = padding_y

        if is_paying:
            # Center Big Icon
            self.icon_payment.setPos((box_w - pay_w) / 2, (box_h - pay_h) / 2)
        else:
            # Stack from Top
            if has_payment:
                self.icon_payment.setPos((box_w - pay_w) / 2, curr_y)
                curr_y += pay_h + spacing_y

            self.text_item.setPos((box_w - txt_w) / 2, curr_y)
            curr_y += txt_h + spacing_y

            if has_handheld:
                self.icon_handheld.setPos((box_w - hh_w) / 2, curr_y)

        # 4. Transform Group
        if self.current_scale > 0.0001:
            # Skalierung etwas anpassen, damit Box nicht riesig wird, wenn sie höher ist
            k = (self.target_size * 0.45) / (box_h * self.current_scale)
            # Begrenzung für k, damit es nicht zu klein wird bei viel Inhalt
            k = max(k, 0.5)

            t = QTransform()
            t.translate(0, -self.pixmap().height() / 2)
            t.scale(k, k)
            # Positionierung über dem Kopf
            t.translate(-box_w / 2, -box_h * 1.5)
            self.info_group.setTransform(t)

        # --- ANIMATION RENDERING ---

        # 1. Pulse Animation (Regal - Aufheben)
        if self.pulse_val > 0:
            self.pulse_val -= 0.1
            if self.pulse_val < 0:
                self.pulse_val = 0
            val = int(255 * self.pulse_val)
            inv = int(80 * (1.0 - self.pulse_val))
            color = QColor(inv, val + inv, inv)
            width = 0.5 + (2.0 * self.pulse_val)
            self.box_bg.setPen(QPen(color, width))
        else:
            if self.box_bg.pen() != self.default_pen:
                self.box_bg.setPen(self.default_pen)

        # 2. Fill Animation (Scan & Pay)
        if self.is_clock_animating:
            # Wenn Paying, etwas langsamer für Effekt? Nein, user will "zufällige Zeit".
            # Die Animation ist rein visuell für den Spieler, der Fortschritt wird logisch in Model getimed.
            # Da wir aber keine Progress-Info vom Model kriegen (nur Start/Ende), machen wir hier eine Fake-Animation
            # die schnell durchläuft.

            self.clock_progress += 0.40  # Speed
            if self.clock_progress >= 1.0:
                self.clock_progress = 1.0
                self.is_clock_animating = False
                self.scan_fill.setPath(QPainterPath())  # Reset
            else:
                fill_height = box_h * self.clock_progress
                fill_rect_path = QPainterPath()
                fill_rect_path.addRect(0, 0, box_w, fill_height)
                final_path = base_path.intersected(fill_rect_path)
                self.scan_fill.setPath(final_path)
        else:
            if not self.scan_fill.path().isEmpty():
                self.scan_fill.setPath(QPainterPath())
