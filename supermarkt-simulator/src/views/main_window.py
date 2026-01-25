"""
Main Window Module.
Serves as the main entry point for the UI.
Updated:
- FIX: Circular Import solved by moving MainController import inside __init__.
- FIX: 'self.sidebar' is correctly assigned for Controller access.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)
from PyQt6.QtCore import Qt

from views.components.sidebar import Sidebar
from views.components.canvas import SimulationCanvas
from views.scene import SimulationScene
from controllers.visual_controller import VisualController
from controllers.interaction_controller import InteractionController
from controllers.map_manager import MapManager
from controllers.simulation_manager import SimulationManager

# WICHTIG: MainController Import hier entfernt, um Zirkelbezug zu vermeiden!


class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Supermarkt Simulator (Berufsschule)")
        self.resize(1400, 900)

        # 1. Central Widget & Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 2. Components
        # self.sidebar muss self gehören, damit InteractionController darauf zugreifen kann
        self.sidebar = Sidebar(self)

        self.scene = SimulationScene(self)
        self.canvas = SimulationCanvas(self.scene)

        # 3. Layout assembly
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.canvas)
        # Sidebar behält ihre Breite, Canvas nimmt den Rest
        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 1)

        # 4. Controllers
        self.map_manager = MapManager(self.settings)
        self.visual_controller = VisualController(self.scene, self.settings)
        self.sim_manager = SimulationManager(self.map_manager, self.settings)

        self.interaction_controller = InteractionController(
            self.scene,
            self.map_manager,
            self.visual_controller,
            self,  # Übergibt MainWindow als 'view'
            self.sim_manager,
        )

        # WICHTIG: Import hier lokal ("Late Import"), damit MainWindow schon existiert
        from controllers.main_controller import MainController

        self.main_controller = MainController(
            self,
            self.map_manager,
            self.visual_controller,
            self.sim_manager,
            self.interaction_controller,
        )

        # 5. Connect UI Signals to MainController
        self._connect_signals()

        # 6. Initial Load
        self.main_controller.start()

    def _connect_signals(self):
        # --- Sidebar / Header ---
        self.sidebar.btn_mode_edit.clicked.connect(
            self.main_controller.switch_to_editor
        )
        self.sidebar.btn_mode_sim.clicked.connect(
            self.main_controller.switch_to_simulation
        )

        # --- Sidebar / Editor / Map ---
        self.sidebar.btn_new_map.clicked.connect(self.main_controller.new_map)
        self.sidebar.btn_save_map.clicked.connect(
            self.main_controller.save_map
        )
        self.sidebar.btn_delete_map.clicked.connect(
            self.main_controller.delete_map
        )
        self.sidebar.map_combo.currentTextChanged.connect(
            self.main_controller.load_map
        )
        self.sidebar.btn_set_background.clicked.connect(
            self.main_controller.set_background
        )
        self.sidebar.btn_remove_background.clicked.connect(
            self.main_controller.remove_background
        )
        self.sidebar.spin_bg_scale.valueChanged.connect(
            self.main_controller.update_bg_scale
        )
        self.sidebar.combo_global_exit.currentTextChanged.connect(
            self.main_controller.set_global_exit
        )

        # --- Sidebar / Editor / Tools ---
        # Wir nutzen Lambdas, um den Tool-String und den Button direkt zu übergeben

        self.sidebar.place_shelves_button.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "shelf", button_ref=self.sidebar.place_shelves_button
            )
        )
        self.sidebar.waiting_area_button.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "waiting_area", button_ref=self.sidebar.waiting_area_button
            )
        )
        self.sidebar.start_area_button.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "start_area", button_ref=self.sidebar.start_area_button
            )
        )
        self.sidebar.btn_exit_area.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "exit_area", button_ref=self.sidebar.btn_exit_area
            )
        )
        self.sidebar.btn_worker_area.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "worker_area", button_ref=self.sidebar.btn_worker_area
            )
        )
        self.sidebar.btn_move_map.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "move_map", button_ref=self.sidebar.btn_move_map
            )
        )

        # Checkouts
        self.sidebar.btn_kl.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "checkout",
                {"type": "Normal", "ori": "Left"},
                self.sidebar.btn_kl,
            )
        )
        self.sidebar.btn_kr.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "checkout",
                {"type": "Normal", "ori": "Right"},
                self.sidebar.btn_kr,
            )
        )
        self.sidebar.btn_sl.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "checkout", {"type": "SB", "ori": "Left"}, self.sidebar.btn_sl
            )
        )
        self.sidebar.btn_sr.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "checkout", {"type": "SB", "ori": "Right"}, self.sidebar.btn_sr
            )
        )

        # Routen
        self.sidebar.new_route_button.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "route", button_ref=self.sidebar.new_route_button
            )
        )
        self.sidebar.btn_start_route.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "start_route", button_ref=self.sidebar.btn_start_route
            )
        )
        self.sidebar.btn_exit_route.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "exit_route", button_ref=self.sidebar.btn_exit_route
            )
        )
        self.sidebar.btn_worker_route.clicked.connect(
            lambda: self.interaction_controller.set_tool(
                "worker_route", button_ref=self.sidebar.btn_worker_route
            )
        )

        # Admin / Confirm (Route fertigstellen)
        self.sidebar.btn_save_admin.clicked.connect(
            self.interaction_controller.finish_route_drawing
        )
        self.sidebar.btn_cancel_route.clicked.connect(
            self.interaction_controller.cancel_route_drawing
        )
        self.sidebar.btn_del_route.clicked.connect(
            self.main_controller.delete_selected_route
        )

        # Objekt Manipulation
        self.sidebar.btn_del_obj.clicked.connect(
            self.main_controller.delete_selected_object
        )
        self.sidebar.btn_edit_obj.clicked.connect(
            self.main_controller.edit_selected_object
        )

        # View Options
        self.sidebar.btn_visibility.clicked.connect(
            self.main_controller.open_visibility_dialog
        )
        self.sidebar.btn_offsets.clicked.connect(
            self.main_controller.open_offset_dialog
        )
        self.sidebar.btn_config_sizes.clicked.connect(
            self.main_controller.open_size_config
        )

    def closeEvent(self, event):
        self.sim_manager.pause()
        event.accept()
