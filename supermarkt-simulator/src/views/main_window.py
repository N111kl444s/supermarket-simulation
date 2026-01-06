"""
Main window module for the application GUI.
Updated: 
- Added ObjectName 'ConfigContent' for styling.
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
    QButtonGroup,
    QTimeEdit,
    QDoubleSpinBox,
    QScrollArea,
    QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QRectF, QTime
from PyQt6.QtGui import QPixmap, QBrush, QColor
import pyqtgraph as pg
from config import *
from .ui_components import ClickablePixmapItem, AutoFitGraphicsView
from .scene import RouteEditorScene
from .styles import get_application_style


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supermarkt Simulator - Workbench")
        self.setGeometry(100, 100, 1600, 900)
        self.is_admin_mode = False

        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_drawing_start_area = False
        self.is_placing_checkout = False
        
        self.is_drawing_start_route = False
        self.is_drawing_exit_route = False
        self.is_drawing_exit_area = False
        
        self.current_checkout_type = "Normal"
        self.current_checkout_orientation = "Right"
        self.highlight_queues = False

        self.sim_scene = RouteEditorScene()
        self.sim_scene.main_window = self
        self.sim_view = None
        self.controller = None

        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(False)
        self.speed_group = QButtonGroup(self)
        self.speed_group.setExclusive(True)

        self.setup_ui()
        self.setStyleSheet(get_application_style())

    def set_controller(self, c):
        self.controller = c

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.create_top_toolbar(main_layout)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        self.sidebar_widget = self.create_sidebar()
        self.splitter.addWidget(self.sidebar_widget)
        self.canvas_widget = self.create_canvas()
        self.splitter.addWidget(self.canvas_widget)
        self.splitter.setSizes([450, 1150]) 
        self.splitter.setCollapsible(0, False)

    def create_top_toolbar(self, parent_layout):
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("ToolbarFrame")
        toolbar_frame.setFixedHeight(70)
        layout = QHBoxLayout(toolbar_frame)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl_mode = QLabel("Modus:")
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(130)
        self.mode_combo.setFixedHeight(30)
        self.mode_combo.addItems(["Simulation", "Editor"])
        self.mode_combo.setStyleSheet(
            f"font-weight: bold; color: {COLOR_TEXT_MAIN.name()};"
        )
        layout.addWidget(lbl_mode)
        layout.addWidget(self.mode_combo)

        self.map_combo = QComboBox()
        self.map_combo.setFixedWidth(180)
        self.map_combo.setFixedHeight(30)
        layout.addWidget(QLabel("Map:"))
        layout.addWidget(self.map_combo)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line1)
        layout.addStretch()

        self.lbl_clock = QLabel("08:00")
        self.lbl_clock.setObjectName("ClockLabel")
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_clock)
        layout.addSpacing(20)

        self.btn_reset = QPushButton("↺")
        self.btn_reset.setObjectName("ToolbarButton")
        self.btn_reset.setFixedWidth(40)
        self.btn_play_pause = QPushButton("▶")
        self.btn_play_pause.setObjectName("ToolbarButton")
        self.btn_play_pause.setCheckable(True)
        self.btn_play_pause.setFixedWidth(50)
        self.btn_play_pause.setStyleSheet(
            f"color: {COLOR_SUCCESS.name()}; font-size: 20px;"
        )
        self.btn_skip = QPushButton("⏭")
        self.btn_skip.setObjectName("ToolbarButton")
        self.btn_skip.setFixedWidth(40)
        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_play_pause)
        layout.addWidget(self.btn_skip)

        layout.addSpacing(15)

        self.btn_speed_1 = QPushButton("1x")
        self.btn_speed_1.setCheckable(True)
        self.btn_speed_1.setChecked(True)
        self.btn_speed_1.setFixedWidth(35)
        self.btn_speed_2 = QPushButton("2x")
        self.btn_speed_2.setCheckable(True)
        self.btn_speed_2.setFixedWidth(35)
        self.btn_speed_3 = QPushButton("6x")
        self.btn_speed_3.setCheckable(True)
        self.btn_speed_3.setFixedWidth(35)
        self.speed_group.addButton(self.btn_speed_1)
        self.speed_group.addButton(self.btn_speed_2)
        self.speed_group.addButton(self.btn_speed_3)
        layout.addWidget(self.btn_speed_1)
        layout.addWidget(self.btn_speed_2)
        layout.addWidget(self.btn_speed_3)
        layout.addStretch()

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line2)
        self.btn_reset_zoom = QPushButton("Ansicht Reset")
        layout.addWidget(self.btn_reset_zoom)
        parent_layout.addWidget(toolbar_frame)

    # --- HELPER UI FUNCTIONS ---
    def _create_distribution_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("color: #6B7280; font-style: italic; font-size: 10px; margin-bottom: 2px;")
        return l

    def _create_header_label(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-weight: bold; color: #374151; margin-top: 5px;")
        return l

    def create_sidebar(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        self.control_tabs = QTabWidget()
        layout.addWidget(self.control_tabs)

        # =========================================================
        # REITER 1: EINGABE (Parameters)
        # =========================================================
        self.tab_input = QWidget()
        scroll_input = QScrollArea()
        scroll_input.setWidgetResizable(True)
        
        content_input = QWidget()
        content_input.setObjectName("ConfigContent") # WICHTIG FÜR CSS
        
        l_input = QVBoxLayout(content_input)
        l_input.setAlignment(Qt.AlignmentFlag.AlignTop)
        l_input.setSpacing(10)

        # --- Öffnungszeiten ---
        gb_time = QGroupBox("Öffnungszeiten")
        f_time = QFormLayout(gb_time)
        self.time_open = QTimeEdit()
        self.time_open.setDisplayFormat("HH:mm")
        self.time_open.setTime(QTime(*DEFAULT_OPEN_TIME))
        self.time_close = QTimeEdit()
        self.time_close.setDisplayFormat("HH:mm")
        self.time_close.setTime(QTime(*DEFAULT_CLOSE_TIME))
        f_time.addRow("Öffnen:", self.time_open)
        f_time.addRow("Schließen:", self.time_close)
        l_input.addWidget(gb_time)

        # --- Kunden ---
        gb_customer = QGroupBox("Kunden Konfiguration")
        l_cust = QVBoxLayout(gb_customer)
        
        # Generierung
        l_cust.addWidget(self._create_header_label("Kundendichte & Generierung"))
        l_cust.addWidget(self._create_distribution_label("(Exponentialverteilung)"))
        
        f_gen = QFormLayout()
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(50)
        self.actor_count_input.setRange(1, 10000)
        self.actor_count_input.setSuffix(" / Tag")
        f_gen.addRow("Anzahl:", self.actor_count_input)
        l_cust.addLayout(f_gen)
        
        # Bewegung
        l_cust.addWidget(self._create_header_label("Bewegungsgeschwindigkeit (px/s)"))
        l_cust.addWidget(self._create_distribution_label("(Normalverteilung)"))
        
        f_move = QFormLayout()
        
        # Walk
        hbox_walk = QHBoxLayout()
        self.speed_walk_mean = QDoubleSpinBox()
        self.speed_walk_mean.setRange(0.1, 20.0)
        self.speed_walk_mean.setValue(2.5)
        self.speed_walk_mean.setSingleStep(0.1)
        self.speed_walk_std = QDoubleSpinBox()
        self.speed_walk_std.setRange(0.0, 5.0)
        self.speed_walk_std.setValue(0.5)
        self.speed_walk_std.setSingleStep(0.1)
        
        hbox_walk.addWidget(QLabel("Ø:"))
        hbox_walk.addWidget(self.speed_walk_mean)
        hbox_walk.addWidget(QLabel("σ:"))
        hbox_walk.addWidget(self.speed_walk_std)
        f_move.addRow("Gehen:", hbox_walk)
        
        # Roll (Disabled)
        hbox_roll = QHBoxLayout()
        self.speed_roll_mean = QDoubleSpinBox()
        self.speed_roll_mean.setRange(0.1, 20.0)
        self.speed_roll_mean.setValue(1.5)
        self.speed_roll_mean.setSingleStep(0.1)
        self.speed_roll_std = QDoubleSpinBox()
        self.speed_roll_std.setRange(0.0, 5.0)
        self.speed_roll_std.setValue(0.3)
        self.speed_roll_std.setSingleStep(0.1)
        
        hbox_roll.addWidget(QLabel("Ø:"))
        hbox_roll.addWidget(self.speed_roll_mean)
        hbox_roll.addWidget(QLabel("σ:"))
        hbox_roll.addWidget(self.speed_roll_std)
        f_move.addRow("Rollen:", hbox_roll)
        
        # Disabled Prob
        self.disabled_prob_input = QDoubleSpinBox()
        self.disabled_prob_input.setRange(0, 100)
        self.disabled_prob_input.setValue(10)
        self.disabled_prob_input.setSuffix(" %")
        f_move.addRow("Behinderungsgrad:", self.disabled_prob_input)
        l_cust.addLayout(f_move)
        
        # Items & Scanning
        l_cust.addWidget(self._create_header_label("Einkauf & Scannen"))
        
        f_shop = QFormLayout()
        
        # Items
        hbox_items = QHBoxLayout()
        self.items_mean = QSpinBox()
        self.items_mean.setRange(1, 100)
        self.items_mean.setValue(12)
        self.items_std = QDoubleSpinBox()
        self.items_std.setRange(0, 20)
        self.items_std.setValue(4.0)
        hbox_items.addWidget(QLabel("Ø:"))
        hbox_items.addWidget(self.items_mean)
        hbox_items.addWidget(QLabel("σ:"))
        hbox_items.addWidget(self.items_std)
        f_shop.addRow("Artikelanzahl:", hbox_items)
        l_cust.addWidget(self._create_distribution_label("(Artikelanzahl: Normalverteilung)"))
        l_cust.addLayout(f_shop)
        
        # Scan Speed
        l_cust.addWidget(QLabel("Scandauer pro Artikel (Sek):"))
        l_cust.addWidget(self._create_distribution_label("(Gleichverteilung)"))
        
        f_scan = QFormLayout()
        
        # Normal Range
        hbox_scan_norm = QHBoxLayout()
        self.scan_speed_normal_min = QDoubleSpinBox()
        self.scan_speed_normal_min.setValue(0.5)
        self.scan_speed_normal_min.setSingleStep(0.1)
        self.scan_speed_normal_max = QDoubleSpinBox()
        self.scan_speed_normal_max.setValue(1.5)
        self.scan_speed_normal_max.setSingleStep(0.1)
        hbox_scan_norm.addWidget(QLabel("Min:"))
        hbox_scan_norm.addWidget(self.scan_speed_normal_min)
        hbox_scan_norm.addWidget(QLabel("Max:"))
        hbox_scan_norm.addWidget(self.scan_speed_normal_max)
        f_scan.addRow("Normal:", hbox_scan_norm)
        
        # Disabled Range
        hbox_scan_dis = QHBoxLayout()
        self.scan_speed_disabled_min = QDoubleSpinBox()
        self.scan_speed_disabled_min.setValue(1.0)
        self.scan_speed_disabled_min.setSingleStep(0.1)
        self.scan_speed_disabled_max = QDoubleSpinBox()
        self.scan_speed_disabled_max.setValue(3.0)
        self.scan_speed_disabled_max.setSingleStep(0.1)
        hbox_scan_dis.addWidget(QLabel("Min:"))
        hbox_scan_dis.addWidget(self.scan_speed_disabled_min)
        hbox_scan_dis.addWidget(QLabel("Max:"))
        hbox_scan_dis.addWidget(self.scan_speed_disabled_max)
        f_scan.addRow("Behindert:", hbox_scan_dis)
        
        l_cust.addLayout(f_scan)
        l_input.addWidget(gb_customer)

        # --- Kassierer ---
        gb_cashier = QGroupBox("Personal (Platzhalter)")
        f_cash = QFormLayout(gb_cashier)
        l_input.addWidget(gb_cashier) 

        # --- Kassen ---
        gb_checkout = QGroupBox("Kassen Eigenschaften")
        f_checkout = QFormLayout(gb_checkout)
        
        self.checkout_fail_rate_normal = QSpinBox()
        self.checkout_fail_rate_normal.setRange(0, 100)
        self.checkout_fail_rate_normal.setSuffix(" %")
        f_checkout.addRow("Ausfall (Normal):", self.checkout_fail_rate_normal)
        
        self.checkout_fail_rate_sb = QSpinBox()
        self.checkout_fail_rate_sb.setRange(0, 100)
        self.checkout_fail_rate_sb.setSuffix(" %")
        f_checkout.addRow("Ausfall (SB):", self.checkout_fail_rate_sb)
        l_input.addWidget(gb_checkout)

        scroll_input.setWidget(content_input)
        self.control_tabs.addTab(scroll_input, "Eingabe")

        # =========================================================
        # REITER 2: SIMULATION
        # =========================================================
        self.tab_simulation = QWidget()
        l_sim = QVBoxLayout(self.tab_simulation)
        
        gb_log = QGroupBox("Live Feed")
        l_log = QVBoxLayout(gb_log)
        self.list_log = QListWidget()
        self.list_log.setAlternatingRowColors(True)
        self.list_log.setStyleSheet("font-size: 11px;")
        l_log.addWidget(self.list_log)
        l_sim.addWidget(gb_log)

        gb_status = QGroupBox("Live Status")
        f_status = QFormLayout(gb_status)
        self.lbl_queue_count = QLabel("0")
        self.lbl_queue_count.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.lbl_customers_in_store = QLabel("0")
        self.lbl_customers_in_store.setStyleSheet("font-weight: bold; font-size: 14px; color: blue;")
        
        f_status.addRow("Kunden in Warteschlange:", self.lbl_queue_count)
        f_status.addRow("Kunden im Laden:", self.lbl_customers_in_store)
        l_sim.addWidget(gb_status)
        
        self.control_tabs.addTab(self.tab_simulation, "Simulation")

        # =========================================================
        # REITER 3: STATISTIKEN
        # =========================================================
        self.tab_stats = QWidget()
        l_stat = QVBoxLayout(self.tab_stats)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_BG_PANEL)
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color=COLOR_TEXT_MAIN))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color=COLOR_TEXT_MAIN))
        l_stat.addWidget(self.plot_widget)
        self.control_tabs.addTab(self.tab_stats, "Statistiken")

        # =========================================================
        # REITER 4: EDITOR
        # =========================================================
        self.tab_config = QWidget()
        l_conf = QVBoxLayout(self.tab_config)
        l_conf.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        gb_map = QGroupBox("Map-Verwaltung")
        l_map_actions = QVBoxLayout(gb_map)
        
        row_map = QHBoxLayout()
        self.btn_new_map = QPushButton("Neu")
        self.btn_save_map = QPushButton("Speichern")
        self.btn_delete_map = QPushButton("Löschen")
        self.btn_delete_map.setStyleSheet(f"color: {COLOR_ERROR.name()}; border-color: {COLOR_ERROR.name()};")
        row_map.addWidget(self.btn_new_map)
        row_map.addWidget(self.btn_save_map)
        row_map.addWidget(self.btn_delete_map)
        l_map_actions.addLayout(row_map)
        
        row_bg = QHBoxLayout()
        self.btn_set_background = QPushButton("🖼️ Bild wählen")
        self.btn_remove_background = QPushButton("❌")
        self.btn_remove_background.setFixedWidth(30)
        row_bg.addWidget(self.btn_set_background)
        row_bg.addWidget(self.btn_remove_background)
        l_map_actions.addLayout(row_bg)

        row_scale = QHBoxLayout()
        row_scale.addWidget(QLabel("Skalierung:"))
        self.spin_bg_scale = QDoubleSpinBox()
        self.spin_bg_scale.setRange(0.1, 10.0)
        self.spin_bg_scale.setSingleStep(0.1)
        self.spin_bg_scale.setValue(1.0)
        row_scale.addWidget(self.spin_bg_scale)
        l_map_actions.addLayout(row_scale)
        l_conf.addWidget(gb_map)

        gb_glob = QGroupBox("Map Einstellungen")
        l_glob = QFormLayout(gb_glob)
        self.combo_global_exit = QComboBox()
        self.combo_global_exit.addItems(["Links", "Rechts", "Oben", "Unten"])
        self.combo_global_exit.setCurrentText("Rechts")
        l_glob.addRow("Abgangsrichtung:", self.combo_global_exit)
        l_conf.addWidget(gb_glob)

        l_conf.addWidget(QLabel("Werkzeuge:"))
        self.start_area_button = QPushButton("1. Startfläche")
        self.start_area_button.setCheckable(True)
        self.btn_start_route = QPushButton("2. Start-Route (Zulauf)")
        self.btn_start_route.setCheckable(True)
        self.new_route_button = QPushButton("3. Shop-Route (Regale)")
        self.new_route_button.setCheckable(True)
        self.place_shelves_button = QPushButton("4. Regale platzieren")
        self.place_shelves_button.setCheckable(True)
        self.waiting_area_button = QPushButton("5. Wartebereich (Kassen)")
        self.waiting_area_button.setCheckable(True)
        self.btn_exit_route = QPushButton("6. Ausgangs-Route")
        self.btn_exit_route.setCheckable(True)
        self.btn_exit_area = QPushButton("7. Ausgangsfläche")
        self.btn_exit_area.setCheckable(True)

        l_conf.addWidget(self.start_area_button)
        l_conf.addWidget(self.btn_start_route)
        l_conf.addWidget(self.new_route_button)
        l_conf.addWidget(self.place_shelves_button)
        l_conf.addWidget(self.waiting_area_button)
        l_conf.addWidget(self.btn_exit_route)
        l_conf.addWidget(self.btn_exit_area)
        
        l_conf.addSpacing(5)
        self.btn_visibility = QPushButton("👁️ Sichtbarkeit")
        self.btn_offsets = QPushButton("📏 Globale Offsets")
        self.btn_config_sizes = QPushButton("⚙️ Größen & Skalierung")
        l_conf.addWidget(self.btn_visibility)
        l_conf.addWidget(self.btn_offsets)
        l_conf.addWidget(self.btn_config_sizes)

        l_conf.addSpacing(15)
        l_conf.addWidget(QLabel("Kasse hinzufügen:"))
        grid_k = QHBoxLayout()
        self.btn_kl = QPushButton("Normal (L)")
        self.btn_kl.setCheckable(True)
        self.btn_kr = QPushButton("Normal (R)")
        self.btn_kr.setCheckable(True)
        self.btn_sl = QPushButton("SB (L)")
        self.btn_sl.setCheckable(True)
        self.btn_sr = QPushButton("SB (R)")
        self.btn_sr.setCheckable(True)
        grid_k.addWidget(self.btn_kl)
        grid_k.addWidget(self.btn_kr)
        grid_k.addWidget(self.btn_sl)
        grid_k.addWidget(self.btn_sr)
        l_conf.addLayout(grid_k)

        self.admin_toolbar = QGroupBox("Route aktiv")
        self.admin_toolbar.setStyleSheet(
            f"border: 1px solid {COLOR_ORANGE.name()}; background-color: {COLOR_BG_PANEL.name()};"
        )
        l_adm = QVBoxLayout(self.admin_toolbar)
        row_adm = QHBoxLayout()
        self.btn_save_admin = QPushButton("Speichern (OK)")
        self.btn_save_admin.setStyleSheet(f"background-color: {COLOR_SUCCESS.name()}; color: white; font-weight: bold;")
        self.btn_cancel_route = QPushButton("Abbrechen")
        self.btn_cancel_route.setStyleSheet(f"color: {COLOR_ERROR.name()}; font-weight: bold;")
        row_adm.addWidget(self.btn_save_admin)
        row_adm.addWidget(self.btn_cancel_route)
        l_adm.addLayout(row_adm)
        l_conf.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()
        
        self.control_tabs.addTab(self.tab_config, "Editor")

        # =========================================================
        # REITER 5: DATEN (Objects)
        # =========================================================
        self.tab_objects = QWidget()
        l_obj = QVBoxLayout(self.tab_objects)
        self.list_tabs = QTabWidget()
        w_routes = QWidget()
        l_r = QVBoxLayout(w_routes)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Route Löschen")
        self.btn_del_route.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(self.btn_del_route)
        self.list_tabs.addTab(w_routes, "Routen")
        w_objs = QWidget()
        l_o = QVBoxLayout(w_objs)
        self.object_list_widget = QListWidget()
        self.btn_edit_obj = QPushButton("Position bearbeiten")
        self.btn_del_obj = QPushButton("Objekt Löschen")
        self.btn_del_obj.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        l_o.addWidget(self.object_list_widget)
        l_o.addWidget(self.btn_edit_obj)
        l_o.addWidget(self.btn_del_obj)
        self.list_tabs.addTab(w_objs, "Items")
        l_obj.addWidget(self.list_tabs)
        self.control_tabs.addTab(self.tab_objects, "Daten")

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

    def add_log_entry(self, message, color="black"):
        self.list_log.insertItem(0, message)
        item = self.list_log.item(0)
        item.setForeground(QBrush(QColor(color)))
        if self.list_log.count() > 100:
            self.list_log.takeItem(100)

    def update_sidebar_mode(self, mode_text):
        is_sim = mode_text == "Simulation"
        
        self.control_tabs.setTabVisible(0, is_sim) # Eingabe
        self.control_tabs.setTabVisible(1, is_sim) # Simulation
        self.control_tabs.setTabVisible(2, is_sim) # Stats
        
        self.control_tabs.setTabVisible(3, not is_sim) # Editor
        self.control_tabs.setTabVisible(4, not is_sim) # Daten
        
        self.control_tabs.setCurrentIndex(0 if is_sim else 3)
        
        self.btn_play_pause.setEnabled(is_sim)
        self.btn_reset.setEnabled(is_sim)
        self.btn_skip.setEnabled(is_sim)
        self.btn_speed_1.setEnabled(is_sim)
        self.btn_speed_2.setEnabled(is_sim)
        self.btn_speed_3.setEnabled(is_sim)
        
        self.time_open.setEnabled(is_sim)
        self.time_close.setEnabled(is_sim)

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