"""
Main window module.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QCheckBox,
    QStackedWidget,
    QListWidget,
    QTableWidget,
    QHeaderView,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPixmap, QBrush

import pyqtgraph as pg

from config import *
from .ui_components import (
    ClickableGroupBox,
    ClickablePixmapItem,
    AutoFitGraphicsView,
)
from .scene import RouteEditorScene


class MainWindow(QMainWindow):
    """
    The main application window.

    Constructs the four-quadrant layout and manages UI state (e.g., admin mode toggle).
    Events are delegated to the controller.

    @ivar controller: Reference to the MainController.
    @type controller: MainController
    @ivar is_sim_maximized: Flag if simulation view is full-screen.
    @type is_sim_maximized: bool
    @ivar is_admin_mode: Flag if admin editing mode is active.
    @type is_admin_mode: bool
    """

    def __init__(self):
        """
        Initializes the main window and its UI components.
        """
        super().__init__()
        self.setWindowTitle("Prototyp 18: Refactoring (MVC 1:1)")
        self.setGeometry(100, 100, 1400, 900)

        # UI State
        self.is_sim_maximized = False
        self.is_q1_maximized = False
        self.is_admin_mode = False
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_placing_checkout = False
        self.current_checkout_type = "Normal"
        self.current_checkout_orientation = "Right"
        self.highlight_queues = False

        self.sim_scene = RouteEditorScene()
        self.sim_scene.main_window = self
        self.sim_view = None
        self.controller = None

        self.setup_ui()

    def set_controller(self, c):
        """
        Injects the controller dependency and connects scene signals.

        @param c: The main controller.
        @type c: MainController
        """
        self.controller = c
        self.sim_scene.clicked_point.connect(
            self.controller.handle_scene_click
        )
        self.sim_scene.waiting_area_created.connect(
            self.controller.handle_waiting_area_created
        )

    def setup_ui(self):
        """
        Constructs the main grid layout (4 quadrants).
        """
        w = QWidget()
        self.setCentralWidget(w)
        ml = QVBoxLayout(w)
        ml.setSpacing(10)
        ml.setContentsMargins(10, 10, 10, 10)

        # Top Row
        self.top_row_widget = QWidget()
        tr = QHBoxLayout(self.top_row_widget)
        tr.setContentsMargins(0, 0, 0, 0)
        self.top_left_group_box = self.create_top_left_quadrant()
        self.top_right_group_box = self.create_top_right_quadrant()
        tr.addWidget(self.top_left_group_box, 1)
        tr.addWidget(self.top_right_group_box, 1)

        # Bottom Row
        self.bottom_row_widget = QWidget()
        br = QHBoxLayout(self.bottom_row_widget)
        br.setContentsMargins(0, 0, 0, 0)
        self.bottom_left_group_box = self.create_bottom_left_quadrant()
        self.bottom_right_group_box = self.create_bottom_right_quadrant()
        br.addWidget(self.bottom_left_group_box, 1)
        br.addWidget(self.bottom_right_group_box, 1)

        ml.addWidget(self.top_row_widget, 1)
        ml.addWidget(self.bottom_row_widget, 1)

    def create_top_left_quadrant(self):
        """
        Creates the 'Controls' quadrant (Top-Left).
        Contains Simulation params and Admin tools in a StackedWidget.

        @return: The configured group box.
        @rtype: QGroupBox
        """
        gb = QGroupBox("Eingabeparameter")
        l = QVBoxLayout(gb)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(10)

        self.admin_mode_checkbox = QCheckBox("Admin-Modus")
        self.admin_mode_checkbox.toggled.connect(self.toggle_admin_mode_ui)
        l.addWidget(self.admin_mode_checkbox)

        self.top_left_stack = QStackedWidget()
        l.addWidget(self.top_left_stack)

        # Page 0: Simulation
        sim_w = QWidget()
        sl = QVBoxLayout(sim_w)
        fl = QFormLayout()
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(10)
        self.actor_count_input.setRange(1, 200)
        fl.addRow("Kunden:", self.actor_count_input)
        sl.addLayout(fl)

        sl.addWidget(QLabel("Kassen:"))
        self.checkout_table = QTableWidget()
        self.checkout_table.setColumnCount(5)
        self.checkout_table.setHorizontalHeaderLabels(
            ["ID", "Typ", "Stat", "Skill", "Max Q"]
        )
        self.checkout_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        sl.addWidget(self.checkout_table)

        self.start_sim_button = QPushButton("Start")
        # Connection handling is done in Controller
        sl.addWidget(self.start_sim_button)

        # Page 1: Admin
        adm_w = QWidget()
        al = QVBoxLayout(adm_w)
        self.settings_button = QPushButton("Layout anpassen...")
        self.new_route_button = QPushButton("Route zeichnen")
        self.place_shelves_button = QPushButton("Regale platzieren")
        self.waiting_area_button = QPushButton("Wartebereich")

        cl = QHBoxLayout()
        self.btn_kl = QPushButton("K(L)")
        self.btn_kr = QPushButton("K(R)")
        self.btn_sl = QPushButton("SB(L)")
        self.btn_sr = QPushButton("SB(R)")
        cl.addWidget(self.btn_kl)
        cl.addWidget(self.btn_kr)
        cl.addWidget(self.btn_sl)
        cl.addWidget(self.btn_sr)

        al.addWidget(self.settings_button)
        al.addWidget(self.new_route_button)
        al.addWidget(self.place_shelves_button)
        al.addWidget(self.waiting_area_button)
        al.addLayout(cl)
        al.addStretch()

        self.top_left_stack.addWidget(sim_w)
        self.top_left_stack.addWidget(adm_w)
        return gb

    def create_top_right_quadrant(self):
        """
        Creates the 'Metrics' quadrant (Top-Right).

        @return: The configured group box.
        @rtype: QGroupBox
        """
        gb = QGroupBox("Ausgabe")
        l = QVBoxLayout(gb)
        values_layout = QFormLayout()

        self.lbl_runtime = QLabel("0.00 s")
        self.lbl_queue_count = QLabel("0")

        values_layout.addRow("Gesamtlaufzeit:", self.lbl_runtime)
        values_layout.addRow("Kunden im Wartebereich:", self.lbl_queue_count)
        l.addLayout(values_layout)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
        l.addWidget(self.plot_widget)
        return gb

    def create_bottom_left_quadrant(self):
        """
        Creates the 'Simulation View' quadrant (Bottom-Left).

        @return: The configured group box.
        @rtype: ClickableGroupBox
        """
        gb = ClickableGroupBox("Simulation")
        gb.clicked.connect(self.toggle_simulation_fullscreen)
        l = QVBoxLayout(gb)

        self.minimize_sim_button = QPushButton("Minimieren")
        self.minimize_sim_button.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        self.minimize_sim_button.hide()
        l.addWidget(self.minimize_sim_button)

        self.minimize_q1_button = QPushButton("Minimieren")
        self.minimize_q1_button.clicked.connect(self.toggle_q1_fullscreen)
        self.minimize_q1_button.hide()
        l.addWidget(self.minimize_q1_button)

        self.admin_toolbar = QWidget()
        tl = QHBoxLayout(self.admin_toolbar)
        self.btn_save_admin = QPushButton("Speichern")
        self.btn_cancel_admin = QPushButton("Abbrechen")
        tl.addWidget(self.btn_save_admin)
        tl.addWidget(self.btn_cancel_admin)
        l.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        l.addWidget(self.sim_view)

        # Load Quadrant Images for 'Zoom' functionality
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
            pass  # Fail silently if images missing

        return gb

    def create_bottom_right_quadrant(self):
        """
        Creates the 'Object Management' quadrant (Bottom-Right).

        @return: The configured group box.
        @rtype: QGroupBox
        """
        gb = QGroupBox("Verwaltung")
        self.bottom_right_stack = QStackedWidget(gb)
        l = QVBoxLayout(gb)
        l.addWidget(self.bottom_right_stack)

        self.bottom_right_stack.addWidget(QTextEdit("Platzhalter..."))

        tabs = QTabWidget()

        # Routes Tab
        w_routes = QWidget()
        l_r = QVBoxLayout(w_routes)
        self.route_list_widget = QListWidget()
        self.btn_del_route = QPushButton("Route löschen")
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(self.btn_del_route)
        tabs.addTab(w_routes, "Routen")

        # Objects Tab
        w_objs = QWidget()
        l_o = QVBoxLayout(w_objs)
        self.object_list_widget = QListWidget()
        self.btn_edit_obj = QPushButton("Position bearbeiten")
        self.btn_del_obj = QPushButton("Objekt entfernen")
        l_o.addWidget(self.object_list_widget)
        l_o.addWidget(self.btn_edit_obj)
        l_o.addWidget(self.btn_del_obj)
        tabs.addTab(w_objs, "Objekte")

        self.bottom_right_stack.addWidget(tabs)
        return gb

    def toggle_admin_mode_ui(self, checked):
        """
        Updates the UI elements based on the admin mode state.

        @param checked: Whether admin mode is active.
        @type checked: bool
        """
        self.is_admin_mode = checked
        if checked:
            if self.is_q1_maximized:
                self.toggle_q1_fullscreen()
            if self.is_sim_maximized:
                self.toggle_simulation_fullscreen()
            self.top_left_stack.setCurrentIndex(1)
            self.bottom_right_stack.setCurrentIndex(1)
            self.bottom_left_group_box.setTitle("Routen-Editor")
            self.bottom_left_group_box.setEnabled(False)
            if hasattr(self, "item_q1"):
                self.item_q1.setEnabled(False)
        else:
            self.top_left_stack.setCurrentIndex(0)
            self.bottom_right_stack.setCurrentIndex(0)
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            self.bottom_left_group_box.setEnabled(True)
            if hasattr(self, "item_q1"):
                self.item_q1.setEnabled(True)

        if self.controller:
            self.controller.toggle_admin_mode_logic(checked)

    def toggle_simulation_fullscreen(self, force=False):
        """
        Toggles the simulation view to fullscreen.

        @param force: Force maximization.
        @type force: bool
        """
        if self.is_q1_maximized:
            self.toggle_q1_fullscreen()
            return
        if self.is_admin_mode and not force:
            return

        self.is_sim_maximized = not self.is_sim_maximized
        if self.is_sim_maximized:
            self.top_row_widget.hide()
            self.bottom_right_group_box.hide()
            self.minimize_sim_button.show()
            self.bottom_left_group_box.setTitle("Live-Simulation (Vollbild)")
        else:
            self.top_row_widget.show()
            self.bottom_right_group_box.show()
            self.minimize_sim_button.hide()
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

    def toggle_q1_fullscreen(self):
        """
        Toggles the zoomed view of Quadrant 1 (Checkouts).
        """
        if not hasattr(self, "item_q1") or self.is_admin_mode:
            return

        self.is_q1_maximized = not self.is_q1_maximized
        if self.is_q1_maximized:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.hide()
            self.minimize_q1_button.show()
            self.sim_view.fitInView(
                self.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
            self.bottom_left_group_box.setTitle("Kassenbereich (Vollbild)")
            if self.is_sim_maximized:
                self.minimize_sim_button.hide()
        else:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.show()
            self.minimize_q1_button.hide()
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )
            if self.is_sim_maximized:
                self.minimize_sim_button.show()
                self.bottom_left_group_box.setTitle(
                    "Live-Simulation (Vollbild)"
                )
            else:
                self.bottom_left_group_box.setTitle(
                    "Live-Simulation (Miniatur)"
                )
