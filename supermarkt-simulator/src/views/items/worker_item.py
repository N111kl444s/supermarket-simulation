"""
Worker Graphics Item.
Displays the maintenance worker.
Optimized for high-quality scaling and correct centering.
Updated:
- FIX: Progress circle visibility using Cosmetic Pen (ignoring scale).
- ADD: Background circle for better contrast.
"""

from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsPathItem,
)
from PyQt6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen, QPainterPath
from PyQt6.QtCore import Qt, QRectF
from config import IMG_WORKER, IMG_TOOL, IMAGE_DIR, ICON_DIR


class WorkerItem(QGraphicsPixmapItem):
    def __init__(self, model, size=32):
        super().__init__()
        self.model = model
        self.target_size = size

        self.setZValue(100)  # Immer sichtbar über allem
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

        # 1. Worker Bild laden
        img_name = IMG_WORKER[0] if IMG_WORKER else "worker.png"
        path = IMAGE_DIR / img_name

        pixmap_loaded = False
        if path.exists():
            original = QPixmap(str(path))
            if not original.isNull():
                self.setPixmap(original)

                # ZENTRIERUNG & SKALIERUNG
                w = original.width()
                h = original.height()
                self.setOffset(-w / 2, -h / 2)

                if w > 0:
                    scale_factor = size / w
                    self.setScale(scale_factor)

                pixmap_loaded = True

        # Fallback
        if not pixmap_loaded:
            fallback = QPixmap(size, size)
            fallback.fill(Qt.GlobalColor.transparent)
            p = QPainter(fallback)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QBrush(QColor("orange")))
            p.drawEllipse(0, 0, size, size)
            p.end()

            self.setPixmap(fallback)
            self.setOffset(-size / 2, -size / 2)

        # 2. Tool Icon setup
        self.tool_item = QGraphicsPixmapItem(self)
        self._load_tool_image()
        self.tool_item.setVisible(False)
        self.tool_item.setZValue(10)

        # 3. Fortschrittsanzeige initialisieren
        self._create_progress_indicator()

        # Initial Position setzen
        self.sync_visuals()

    def _load_tool_image(self):
        p1 = ICON_DIR / IMG_TOOL
        p2 = IMAGE_DIR / IMG_TOOL
        path = p1 if p1.exists() else p2

        pix = QPixmap()
        loaded = False
        if path.exists():
            loaded = pix.load(str(path))

        if not loaded or pix.isNull():
            # Fallback Tool: Cyan Kreis
            tsize = int(self.target_size * 0.8)
            pix = QPixmap(tsize, tsize)
            pix.fill(Qt.GlobalColor.transparent)
            p = QPainter(pix)
            p.setBrush(QBrush(QColor("cyan")))
            p.drawEllipse(0, 0, tsize, tsize)
            p.end()

        # Tool relativ zum ORIGINAL-Worker-Bild skalieren
        base_w = self.pixmap().width()
        target_tool_w = int(base_w * 0.6)
        if target_tool_w < 1:
            target_tool_w = 10

        pix_scaled = pix.scaled(
            target_tool_w,
            target_tool_w,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.tool_item.setPixmap(pix_scaled)

        # Position: Mittig, über dem Kopf
        self.tool_item.setPos(
            -pix_scaled.width() / 2,
            -self.pixmap().height() / 2 - pix_scaled.height() * 0.8,
        )

    def _create_progress_indicator(self):
        """Erstellt die Grafik-Items für den Ladekreis."""

        # 3a. Hintergrund-Ring (Dunkelgrau)
        self.progress_bg_item = QGraphicsPathItem(self.tool_item)
        pen_bg = QPen(QColor(60, 60, 60))
        pen_bg.setWidth(4)  # Breite in Bildschirm-Pixeln
        pen_bg.setCosmetic(True)  # WICHTIG: Ignoriert Skalierung
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.progress_bg_item.setPen(pen_bg)
        self.progress_bg_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.progress_bg_item.setZValue(11)

        # 3b. Vordergrund-Ring (Grün)
        self.progress_item = QGraphicsPathItem(self.tool_item)
        pen_fg = QPen(QColor(0, 255, 0))  # Hellgrün
        pen_fg.setWidth(4)  # Breite in Bildschirm-Pixeln
        pen_fg.setCosmetic(True)  # WICHTIG: Ignoriert Skalierung
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.progress_item.setPen(pen_fg)
        self.progress_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.progress_item.setZValue(12)

    def sync_visuals(self):
        # Position vom Modell übernehmen
        self.setPos(self.model.pos)

        # Worker bleibt aufrecht (keine Rotation)

        # Status prüfen
        if self.model.state == "REPAIRING":
            if not self.tool_item.isVisible():
                self.tool_item.setVisible(True)
                self.progress_bg_item.setVisible(True)
                self.progress_item.setVisible(True)

            # --- Fortschrittsanzeige Update ---
            duration = self.model.repair_duration_total
            timer = self.model.repair_timer

            if duration > 0:
                percent = min(1.0, max(0.0, timer / duration))

                # Wir zeichnen den Kreis relativ zur Mitte des Tools
                t_w = self.tool_item.pixmap().width()
                t_h = self.tool_item.pixmap().height()

                # Rechteck für den Kreis (etwas größer als das Tool)
                # Da Cosmetic Pen genutzt wird, müssen wir den Margin nicht riesig machen,
                # aber er bezieht sich auf das Koordinatensystem des Bildes.
                margin = t_w * 0.1
                rect = QRectF(
                    -margin, -margin, t_w + 2 * margin, t_h + 2 * margin
                )

                # Hintergrund (voller Kreis)
                path_bg = QPainterPath()
                path_bg.addEllipse(rect)
                self.progress_bg_item.setPath(path_bg)

                # Vordergrund (Arc)
                path_fg = QPainterPath()
                # Start bei 90 Grad (12 Uhr)
                path_fg.arcMoveTo(rect, 90)
                path_fg.arcTo(rect, 90, -(percent * 360))
                self.progress_item.setPath(path_fg)

        else:
            if self.tool_item.isVisible():
                self.tool_item.setVisible(False)
                self.progress_bg_item.setVisible(False)
                self.progress_item.setVisible(False)
                # Pfad leeren
                self.progress_item.setPath(QPainterPath())
                self.progress_bg_item.setPath(QPainterPath())
