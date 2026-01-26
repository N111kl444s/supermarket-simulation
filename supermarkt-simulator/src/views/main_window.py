"""
Main window module.
Refactored:
- FIX: 'SimulationCanvas' IS the view.
- FIX: Updated references to Sidebar conflict resolution parameters to avoid AttributeError.
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

from .styles import get_application_style
from .components.toolbar import TopToolbar
from .components.sidebar import Sidebar
from .components.canvas import SimulationCanvas


class MainWindow(QMainWindow):
    """
    Das Hauptfenster der Anwendung.
    Es koordiniert Toolbar, Sidebar und den Simulations-Canvas.
    """

    def __init__(self):
        """
        Initialisiert das Fenster und seine Komponenten.
        """
        super().__init__()
        self.setWindowTitle("Supermarkt Simulator - Workbench")

        # States
        self.is_admin_mode = False
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_drawing_start_area = False
        self.is_drawing_worker_area = False
        self.is_placing_checkout = False
        self.is_drawing_start_route = False
        self.is_drawing_exit_route = False
        self.is_drawing_exit_area = False

        self.setup_ui()
        self.setStyleSheet(get_application_style())
        self._expose_ui_elements()

        # Scene connection
        if hasattr(self.canvas_component, "sim_scene"):
            self.sim_scene = self.canvas_component.sim_scene
            self.sim_scene.main_window = self

    def set_controller(self, c):
        """
        Setzt den Controller für das Fenster.

        @type c: MainController
        @param c: Die Instanz des Haupt-Controllers.
        """
        self.controller = c

    def setup_ui(self):
        """
        Baut das Layout des Hauptfensters auf.
        """
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root_layout.addWidget(splitter)

        self.sidebar_component = Sidebar()
        splitter.addWidget(self.sidebar_component)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.toolbar_component = TopToolbar()
        right_layout.addWidget(self.toolbar_component)

        self.canvas_component = SimulationCanvas(self)
        right_layout.addWidget(self.canvas_component)

        splitter.addWidget(right_container)
        splitter.setSizes([350, 1250])
        splitter.setCollapsible(0, False)

    def _expose_ui_elements(self):
        """
        Verknüpft die UI-Elemente der Komponenten direkt mit dem Hauptfenster.
        Behebt den AttributeError durch Zuweisung der neuen Sidebar-Attribute.
        """
        t = self.toolbar_component
        s = self.sidebar_component

        # Sidebar Controls
        self.mode_combo = s.mode_combo
        self.map_combo = s.map_combo
        self.main_tabs = s.main_tabs

        # Toolbar Controls
        self.clock_widget = t.clock_widget
        self.btn_reset = t.btn_reset
        self.btn_play_pause = t.btn_play_pause
        self.btn_skip = t.btn_skip
        self.btn_speed_1 = t.btn_speed_1
        self.btn_speed_2 = t.btn_speed_2
        self.btn_speed_3 = t.btn_speed_3
        self.btn_reset_zoom = t.btn_reset_zoom
        self.speed_group = t.speed_group

        # Sidebar Inputs & Logic
        self.time_open = s.time_open
        self.time_close = s.time_close
        self.actor_count_input = s.actor_count_input
        self.disabled_prob_input = s.disabled_prob_input
        self.speed_walk_mean = s.speed_walk_mean
        self.speed_walk_std = s.speed_walk_std
        self.speed_roll_mean = s.speed_roll_mean
        self.speed_roll_std = s.speed_roll_std
        self.items_mean = s.items_mean
        self.items_std = s.items_std
        self.hand_scanner_prob = s.hand_scanner_prob
        self.scan_speed_normal_min = s.scan_speed_normal_min
        self.scan_speed_normal_max = s.scan_speed_normal_max
        self.scan_speed_disabled_min = s.scan_speed_disabled_min
        self.scan_speed_disabled_max = s.scan_speed_disabled_max
        self.scan_speed_newbie_min = s.scan_speed_newbie_min
        self.scan_speed_newbie_max = s.scan_speed_newbie_max
        self.scan_speed_pro_min = s.scan_speed_pro_min
        self.scan_speed_pro_max = s.scan_speed_pro_max
        self.checkout_fail_rate_normal = s.checkout_fail_rate_normal
        self.checkout_fail_rate_sb = s.checkout_fail_rate_sb

        # FIX: Neue Konflikt-Variablen aus der Sidebar
        self.conflict_solve_newbie_min = s.conflict_solve_newbie_min
        self.conflict_solve_newbie_max = s.conflict_solve_newbie_max
        self.conflict_solve_pro_min = s.conflict_solve_pro_min
        self.conflict_solve_pro_max = s.conflict_solve_pro_max
        self.customer_annoyance_rate = s.customer_annoyance_rate

        self.list_log = s.list_log
        self.lbl_queue_count = s.lbl_queue_count
        self.lbl_customers_in_store = s.lbl_customers_in_store
        self.lbl_total_customers = s.lbl_total_customers
        self.gb_stats = s.gb_stats
        self.plot_widget = s.plot_widget

        self.btn_new_map = s.btn_new_map
        self.btn_save_map = s.btn_save_map
        self.btn_delete_map = s.btn_delete_map
        self.btn_set_background = s.btn_set_background
        self.btn_remove_background = s.btn_remove_background
        self.spin_bg_scale = s.spin_bg_scale
        self.combo_global_exit = s.combo_global_exit
        self.btn_move_map = s.btn_move_map

        self.start_area_button = s.start_area_button
        self.waiting_area_button = s.waiting_area_button
        self.btn_exit_area = s.btn_exit_area
        self.btn_worker_area = s.btn_worker_area
        self.btn_visibility = s.btn_visibility
        self.btn_offsets = s.btn_offsets
        self.btn_config_sizes = s.btn_config_sizes

        self.btn_start_route = s.btn_start_route
        self.new_route_button = s.new_route_button
        self.btn_exit_route = s.btn_exit_route
        self.admin_toolbar = s.admin_toolbar
        self.btn_save_admin = s.btn_save_admin
        self.btn_cancel_route = s.btn_cancel_route
        self.route_list_widget = s.route_list_widget
        self.btn_del_route = s.btn_del_route

        self.place_shelves_button = s.place_shelves_button
        self.btn_kl = s.btn_kl
        self.btn_kr = s.btn_kr
        self.btn_sl = s.btn_sl
        self.btn_sr = s.btn_sr
        self.object_list_widget = s.object_list_widget
        self.btn_edit_obj = s.btn_edit_obj
        self.btn_del_obj = s.btn_del_obj

        self.sim_view = self.canvas_component

    def add_log_entry(self, message, color="black"):
        """
        Fügt einen Eintrag in das Ereignis-Log ein.

        @type message: str
        @param message: Der Text.
        @type color: str
        @param color: Die Farbe des Eintrags.
        """
        self.list_log.insertItem(0, message)
        item = self.list_log.item(0)
        item.setForeground(QBrush(QColor(color)))
        if self.list_log.count() > 100:
            self.list_log.takeItem(100)

    def update_sidebar_mode(self, mode_text):
        """
        Schaltet die Sidebar-Ansicht um.

        @type mode_text: str
        @param mode_text: 'Simulation' oder 'Editor'.
        """
        is_sim = mode_text == "Simulation"
        if is_sim:
            self.main_tabs.setTabVisible(0, True)
            self.main_tabs.setTabVisible(1, True)
            self.main_tabs.setTabVisible(2, False)
            self.main_tabs.setCurrentIndex(0)
        else:
            self.main_tabs.setTabVisible(0, False)
            self.main_tabs.setTabVisible(1, False)
            self.main_tabs.setTabVisible(2, True)
            self.main_tabs.setCurrentIndex(2)

        self.btn_play_pause.setEnabled(is_sim)
        self.btn_reset.setEnabled(is_sim)
        self.btn_skip.setEnabled(is_sim)
        self.btn_speed_1.setEnabled(is_sim)
        self.btn_speed_2.setEnabled(is_sim)
        self.btn_speed_3.setEnabled(is_sim)
        self.time_open.setEnabled(is_sim)
        self.time_close.setEnabled(is_sim)

    def reset_sim_zoom(self, target_center=None):
        """
        Setzt den Zoom des Simulation-Canvas zurück.
        """
        if self.sim_view:
            self.sim_view.reset_zoom(target_center)
