"""
Simulation Canvas Component.
Handles the Scene and GraphicsView.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QBrush, QPixmap
from config import COLOR_FLOOR, IMAGE_DIR
from views.scene import RouteEditorScene
from views.ui_components import AutoFitGraphicsView, ClickablePixmapItem

class SimulationCanvas(QWidget):
    def __init__(self, main_window_ref, parent=None):
        super().__init__(parent)
        self.mw = main_window_ref # Referenz auf MainWindow (für State)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.sim_scene = RouteEditorScene()
        self.sim_scene.main_window = self.mw
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_FLOOR))
        
        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        self.sim_view.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.sim_view)

        # Standard Quadranten laden (Fallback)
        try:
            self.item_q1 = ClickablePixmapItem(QPixmap(str(IMAGE_DIR / "quadrant_1.png")))
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(self.toggle_q1_fullscreen)
            
            # WICHTIG: Referenz im MainWindow setzen für AutoFit-Logik
            self.mw.item_q1 = self.item_q1

            self.item_q2 = self.sim_scene.addPixmap(QPixmap(str(IMAGE_DIR / "quadrant_2.png")))
            self.item_q2.setPos(800, 0)
            self.item_q3 = self.sim_scene.addPixmap(QPixmap(str(IMAGE_DIR / "quadrant_3.png")))
            self.item_q3.setPos(0, 450)
            self.item_q4 = self.sim_scene.addPixmap(QPixmap(str(IMAGE_DIR / "quadrant_4.png")))
            self.item_q4.setPos(800, 450)

            self.scene_rect = QRectF(0, 0, 1600, 900)
            self.sim_scene.setSceneRect(self.scene_rect)
            self.sim_view.fitInView(self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio)
        except Exception:
            pass

    def toggle_q1_fullscreen(self):
        if self.mw.is_admin_mode: return
        
        # State auf MainWindow toggeln, da View dort prüft
        self.mw.is_q1_maximized = not getattr(self.mw, "is_q1_maximized", False)
        
        # Reset Zoom ruft _apply_auto_fit auf, welches den neuen State nutzt
        self.sim_view.reset_zoom()
        
        items = [self.item_q2, self.item_q3, self.item_q4]
        if self.mw.is_q1_maximized:
            for i in items: i.hide()
            # Der explizite fitInView Aufruf passiert jetzt im reset_zoom() via _apply_auto_fit
        else:
            for i in items: i.show()