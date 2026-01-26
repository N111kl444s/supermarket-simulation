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

        self.tool_icon = None  # For repair animation

        self.setZValue(25)
        self.setAcceptHoverEvents(True)

        # Create info box (always visible, like CustomerItem)
        self._create_info_box()

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
        """Shows or hides the repair/conflict icon in the always-visible info box above the cashier."""
        self.icon_name = icon_name if is_repairing else None
        
        # Load and show icon if repairing/conflicting, hide if not
        if is_repairing and icon_name:
            icon_path = ICON_DIR / icon_name
            tool_pixmap = QPixmap(str(icon_path))
            if not tool_pixmap.isNull():
                # Scale icon to 80% of box height
                target_h = 16 * 0.8
                scale_tool = min(1.0, target_h / tool_pixmap.height())
                scaled_pixmap = tool_pixmap.scaled(
                    int(tool_pixmap.width() * scale_tool),
                    int(tool_pixmap.height() * scale_tool),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.tool_icon.setPixmap(scaled_pixmap)
                # Center the icon in the box
                icon_rect = self.tool_icon.boundingRect()
                self.tool_icon.setPos((16 - icon_rect.width()) / 2, (16 - icon_rect.height()) / 2)
                self.tool_icon.setVisible(True)
            else:
                self.tool_icon.setVisible(False)
        else:
            self.tool_icon.setVisible(False)

    def set_repair_progress(self, progress: float):
        """Animiert die grüne Progress-Anzeige wie beim Kunden (scan_fill), von oben nach unten in der quadratischen Box."""
        from PyQt6.QtGui import QPainterPath
        if not hasattr(self, 'info_group') or self.info_group is None:
            return
        if not hasattr(self, 'scan_fill') or self.scan_fill is None:
            return
        box_bg = self.box_bg if hasattr(self, 'box_bg') else None
        if not box_bg:
            return
        box_rect = box_bg.boundingRect()
        box_w, box_h = box_rect.width(), box_rect.height()
        base_path = box_bg.path() if hasattr(box_bg, 'path') else QPainterPath()
        if progress is None or progress <= 0.0:
            self.scan_fill.setPath(QPainterPath())
            return
        fill_height = box_h * progress
        fill_rect_path = QPainterPath()
        fill_rect_path.addRect(0, 0, box_w, fill_height)
        final_path = base_path.intersected(fill_rect_path)
        self.scan_fill.setPath(final_path)

    def setPos(self, *args, **kwargs):
        super().setPos(*args, **kwargs)
        self._update_info_box_position()

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

    def _create_info_box(self):
        """Create info box always (like CustomerItem), but only show icon when needed."""
        self.info_group = QGraphicsItemGroup(self)
        self.info_group.setZValue(200)

        # 1. Background (always create, but may be invisible)
        self.box_bg = QGraphicsPathItem()
        box_w = box_h = 16
        base_path = QPainterPath()
        base_path.addRoundedRect(0, 0, box_w, box_h, 3, 3)
        self.box_bg.setPath(base_path)
        self.box_bg.setBrush(QBrush(QColor(255, 255, 255, 230)))
        self.default_pen = QPen(QColor(80, 80, 80), 0.5)
        self.box_bg.setPen(self.default_pen)
        self.info_group.addToGroup(self.box_bg)

        # 1b. Progress Animation Overlay
        self.scan_fill = QGraphicsPathItem()
        self.scan_fill.setBrush(QBrush(QColor(16, 185, 129, 120)))  # Green for repair
        self.scan_fill.setPen(QPen(Qt.PenStyle.NoPen))
        self.info_group.addToGroup(self.scan_fill)

        # 2. Icon (only visible when icon_name is set)
        self.tool_icon = QGraphicsPixmapItem()
        self.info_group.addToGroup(self.tool_icon)

        # Position box above cashier (like CustomerItem)
        self._update_info_box_position()

    def _update_info_box_position(self):
        """Positions the info box above the cashier, like the customer info box."""
        if hasattr(self, 'info_group') and self.info_group:
            # Position above the cashier
            cashier_rect = self.boundingRect()
            box_x = cashier_rect.center().x() - 8  # Center horizontally (box is 16 wide)
            box_y = cashier_rect.top() - 20  # Above the cashier
            self.info_group.setPos(box_x, box_y)
