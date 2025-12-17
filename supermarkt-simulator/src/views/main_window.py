"""
Main window module for the application GUI.
Refactored: Split Settings button into Visibility and Offsets buttons.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QListWidget,
    QTabWidget,
    QComboBox,
    QSplitter,
    QFrame,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QBrush, QColor

import pyqtgraph as pg

from config import *
from .ui_components import (
    ClickablePixmapItem,
    AutoFitGraphicsView,
)
from .scene import RouteEditorScene
from .styles import get_application_style


class MainWindow(QMainWindow):
    """
    The main application window using a modern 'Workbench' layout.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supermarkt Simulator - Workbench")
        self.setGeometry(100, 100, 1600, 900)

        # Flags for Editor State
        self.is_admin_mode = False
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_placing_checkout = False
        self.current_checkout_type = "Normal"
        self.current_checkout_orientation = "Right"
        self.highlight_queues = False

        # Scene Setup
        self.sim_scene = RouteEditorScene()
        self.sim_scene.main_window = self
        self.sim_view = None
        self.controller = None

        self.setup_ui()
        self.setStyleSheet(get_application_style())

    def set_controller(self, c):
        self.controller = c

    def setup_ui(self):
        # Central Widget Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. TOP TOOLBAR AREA
        self.create_top_toolbar(main_layout)

        # 2. CONTENT AREA (Splitter)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # 2a. Left Sidebar
        self.sidebar_widget = self.create_sidebar()
        self.splitter.addWidget(self.sidebar_widget)

        # 2b. Main Canvas (Simulation)
        self.canvas_widget = self.create_canvas()
        self.splitter.addWidget(self.canvas_widget)

        self.splitter.setSizes([350, 1250])
        self.splitter.setCollapsible(0, False)

    def create_top_toolbar(self, parent_layout):
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("ToolbarFrame")
        toolbar_frame.setFixedHeight(70)

        layout = QHBoxLayout(toolbar_frame)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # -- Left: Map Selection --
        lbl_map = QLabel("Map:")
        lbl_map.setFixedHeight(30)

        self.map_combo = QComboBox()
        self.map_combo.setFixedWidth(250)
        self.map_combo.setFixedHeight(30)

        layout.addWidget(lbl_map)
        layout.addWidget(self.map_combo)

        # -- Center: Simulation Control --
        layout.addStretch()
        self.start_sim_button = QPushButton("Simulation Starten")
        self.start_sim_button.setFixedWidth(220)
        self.start_sim_button.setFixedHeight(36)

        self.start_sim_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLOR_SUCCESS.name()}; 
                color: white; 
                font-weight: bold; 
                border: none;
                border-radius: 4px;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #059669; 
                margin-top: 1px; 
            }}
        """
        )

        layout.addWidget(self.start_sim_button)

        layout.addStretch()

        # -- Right: View Controls --
        self.btn_reset_zoom = QPushButton("Ansicht zurücksetzen")
        self.btn_reset_zoom.setFixedHeight(30)
        layout.addWidget(self.btn_reset_zoom)

        parent_layout.addWidget(toolbar_frame)

    def create_sidebar(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)

        self.control_tabs = QTabWidget()
        layout.addWidget(self.control_tabs)

        # --- TAB 1: SIMULATION ---
        self.tab_sim = QWidget()
        l_sim = QVBoxLayout(self.tab_sim)
        l_sim.setAlignment(Qt.AlignmentFlag.AlignTop)

        gb_params = QGroupBox("Parameter")
        f_params = QFormLayout(gb_params)
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(10)
        self.actor_count_input.setRange(1, 500)
        f_params.addRow("Kundenanzahl:", self.actor_count_input)
        l_sim.addWidget(gb_params)

        l_sim.addWidget(
            QLabel(
                "<i>Tipp: Klicke auf eine Kasse,<br>um sie zu konfigurieren.</i>"
            )
        )

        l_sim.addSpacing(10)
        gb_mini_metrics = QGroupBox("Status")
        l_mm = QFormLayout(gb_mini_metrics)
        self.lbl_runtime = QLabel("0.00 s")
        self.lbl_queue_count = QLabel("0")
        l_mm.addRow("Laufzeit:", self.lbl_runtime)
        l_mm.addRow("Warteschlange:", self.lbl_queue_count)
        l_sim.addWidget(gb_mini_metrics)

        self.control_tabs.addTab(self.tab_sim, "Sim")

        # --- TAB 2: EDITOR ---
        self.tab_config = QWidget()
        l_conf = QVBoxLayout(self.tab_config)
        l_conf.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Map Management
        gb_map = QGroupBox("Map-Verwaltung")
        l_map_actions = QHBoxLayout(gb_map)
        self.btn_new_map = QPushButton("Neu")
        self.btn_save_map = QPushButton("Speichern")
        self.btn_delete_map = QPushButton("Löschen")
        self.btn_delete_map.setStyleSheet(
            f"color: {COLOR_ERROR.name()}; border-color: {COLOR_ERROR.name()};"
        )

        l_map_actions.addWidget(self.btn_new_map)
        l_map_actions.addWidget(self.btn_save_map)
        l_map_actions.addWidget(self.btn_delete_map)
        l_conf.addWidget(gb_map)

        # Tools
        l_conf.addWidget(QLabel("Werkzeuge:"))
        self.new_route_button = QPushButton("Route zeichnen")
        self.place_shelves_button = QPushButton("Regale platzieren")
        self.waiting_area_button = QPushButton("Wartebereich")

        # New split buttons for Settings
        self.btn_visibility = QPushButton("👁️ Sichtbarkeit")
        self.btn_offsets = QPushButton("📏 Globale Offsets")

        l_conf.addWidget(self.new_route_button)
        l_conf.addWidget(self.place_shelves_button)
        l_conf.addWidget(self.waiting_area_button)
        l_conf.addSpacing(5)
        l_conf.addWidget(self.btn_visibility)
        l_conf.addWidget(self.btn_offsets)

        l_conf.addSpacing(15)
        l_conf.addWidget(QLabel("Kasse hinzufügen:"))
        grid_k = QHBoxLayout()
        self.btn_kl = QPushButton("Normal (L)")
        self.btn_kr = QPushButton("Normal (R)")
        self.btn_sl = QPushButton("SB (L)")
        self.btn_sr = QPushButton("SB (R)")

        grid_k.addWidget(self.btn_kl)
        grid_k.addWidget(self.btn_kr)
        grid_k.addWidget(self.btn_sl)
        grid_k.addWidget(self.btn_sr)
        l_conf.addLayout(grid_k)

        # Editor Action Toolbar
        self.admin_toolbar = QGroupBox("Aktion aktiv")
        self.admin_toolbar.setStyleSheet(
            f"border: 1px solid {COLOR_ORANGE.name()};"
        )
        l_adm = QVBoxLayout(self.admin_toolbar)
        self.btn_save_admin = QPushButton("Bestätigen")
        self.btn_save_admin.setStyleSheet(
            f"color: {COLOR_SUCCESS.name()}; font-weight: bold;"
        )
        self.btn_cancel_admin = QPushButton("Abbrechen")
        self.btn_cancel_admin.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_adm.addWidget(self.btn_save_admin)
        l_adm.addWidget(self.btn_cancel_admin)

        l_conf.addSpacing(20)
        l_conf.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        self.control_tabs.addTab(self.tab_config, "Editor")

        # --- TAB 3: DATEN ---
        self.tab_objects = QWidget()
        l_obj = QVBoxLayout(self.tab_objects)

        self.list_tabs = QTabWidget()

        w_routes = QWidget()
        l_r = QVBoxLayout(w_routes)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Löschen")
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(self.btn_del_route)
        self.list_tabs.addTab(w_routes, "Routen")

        w_objs = QWidget()
        l_o = QVBoxLayout(w_objs)
        self.object_list_widget = QListWidget()
        self.btn_edit_obj = QPushButton("Verschieben")
        self.btn_del_obj = QPushButton("Löschen")
        l_o.addWidget(self.object_list_widget)
        l_o.addWidget(self.btn_edit_obj)
        l_o.addWidget(self.btn_del_obj)
        self.list_tabs.addTab(w_objs, "Items")

        l_obj.addWidget(self.list_tabs)
        self.control_tabs.addTab(self.tab_objects, "Daten")

        # --- TAB 4: STATISTIK ---
        self.tab_stats = QWidget()
        l_stat = QVBoxLayout(self.tab_stats)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_BG_PANEL)
        self.plot_widget.getAxis("bottom").setPen(
            pg.mkPen(color=COLOR_TEXT_MAIN)
        )
        self.plot_widget.getAxis("left").setPen(
            pg.mkPen(color=COLOR_TEXT_MAIN)
        )
        l_stat.addWidget(self.plot_widget)
        self.control_tabs.addTab(self.tab_stats, "Stats")

        return container

    def create_canvas(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sim_scene.setBackgroundBrush(QBrush(COLOR_FLOOR))
        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        self.sim_view.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.sim_view)

        try:
            self.item_q1 = ClickablePixmapItem(
                QPixmap(str(IMAGE_DIR / "quadrant_1.png"))
            )
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(self.toggle_q1_fullscreen)

            self.item_q2 = self.sim_scene.addPixmap(
                QPixmap(str(IMAGE_DIR / "quadrant_2.png"))
            )
            self.item_q2.setPos(800, 0)
            self.item_q3 = self.sim_scene.addPixmap(
                QPixmap(str(IMAGE_DIR / "quadrant_3.png"))
            )
            self.item_q3.setPos(0, 450)
            self.item_q4 = self.sim_scene.addPixmap(
                QPixmap(str(IMAGE_DIR / "quadrant_4.png"))
            )
            self.item_q4.setPos(800, 450)

            self.scene_rect = QRectF(0, 0, 1600, 900)
            self.sim_scene.setSceneRect(self.scene_rect)
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )
        except Exception:
            pass

        return container

    def toggle_q1_fullscreen(self):
        if not hasattr(self, "item_q1") or self.is_admin_mode:
            return

        self.is_q1_maximized = not getattr(self, "is_q1_maximized", False)
        self.reset_sim_zoom()

        if self.is_q1_maximized:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.hide()
            self.sim_view.fitInView(
                self.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
        else:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.show()
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

    def reset_sim_zoom(self):
        if self.sim_view:
            self.sim_view.reset_zoom()
