"""
Main Controller.
Orchestrates the application by connecting specialized controllers.
Refactored: Added connection for Reset Zoom button.
"""

from PyQt6.QtWidgets import QMessageBox, QInputDialog, QFileDialog, QListWidgetItem, QGraphicsView
from PyQt6.QtCore import Qt

from config import DEFAULT_SETTINGS, SETTINGS_FILE, MAPS_DIR, IMAGE_DIR, FACTOR_1X, FACTOR_2X, FACTOR_6X, CASHIER_SIZE
from views.main_window import MainWindow

# Core Sub-Controllers
from controllers.map_manager import MapManager
from controllers.simulation_manager import SimulationManager
from controllers.visual_controller import VisualController
from controllers.interaction_controller import InteractionController

# UI & Dialogs
from views.dialogs import VisibilityDialog, OffsetDialog
from views.size_config_dialog import SizeConfigDialog

class MainController:
    """
    Hauptsteuerung der Anwendung. Delegiert Aufgaben an Sub-Controller.
    """
    def __init__(self):
        # 1. UI Setup
        self.view = MainWindow()
        self.view.set_controller(self)
        self.scene = self.view.sim_scene
        
        # 2. Settings & Data
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings_file = SETTINGS_FILE
        self._load_settings()

        # 3. Initialize Managers
        self.map_manager = MapManager()
        self.sim_manager = SimulationManager(self.map_manager, self.settings)
        self.visual_controller = VisualController(self.scene, self.settings)
        
        self.interaction_controller = InteractionController(
            self.scene, 
            self.map_manager, 
            self.visual_controller, 
            self.view, 
            self.sim_manager
        )
        
        self.selected_object_spec = None
        
        # 4. Connect All Signals
        self._connect_ui_signals()
        
        # 5. Boot
        self._refresh_map_list()
        self.on_mode_changed("Simulation")
        self.sim_manager.time_updated.emit(self.sim_manager.sim_time.toString("HH:mm"))
        self.sim_manager.set_param_accessor(self._get_sim_params_from_ui)

        if self.view.sim_view:
            self.view.sim_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def show(self):
        self.view.show()

    def _load_settings(self):
        if self.settings_file.exists():
            import json
            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))
        if self.settings.get("size_cashier", 22) < 40:
            self.settings["size_cashier"] = CASHIER_SIZE

    def _connect_ui_signals(self):
        # Simulation
        self.view.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.view.btn_reset.clicked.connect(self.reset_simulation)
        self.view.btn_skip.clicked.connect(self.sim_manager.skip_day)
        
        self.view.btn_speed_1.clicked.connect(lambda: self.sim_manager.set_time_factor(FACTOR_1X)) 
        self.view.btn_speed_2.clicked.connect(lambda: self.sim_manager.set_time_factor(FACTOR_2X))
        self.view.btn_speed_3.clicked.connect(lambda: self.sim_manager.set_time_factor(FACTOR_6X))
        
        # FIX: Reset Zoom Button verbinden
        self.view.btn_reset_zoom.clicked.connect(self.view.reset_sim_zoom)
        
        self.sim_manager.time_updated.connect(self.view.lbl_clock.setText)
        self.sim_manager.stats_updated.connect(lambda w, c, t: (
            self.view.lbl_queue_count.setText(str(w)), 
            self.view.lbl_customers_in_store.setText(str(c)),
            self.view.lbl_total_customers.setText(str(t))
        ))
        self.sim_manager.log_message.connect(self.view.add_log_entry)
        self.sim_manager.day_finished.connect(lambda: QMessageBox.information(self.view, "Info", "Tag beendet."))
        
        # Visueller Sync
        self.sim_manager.sim_timer.timeout.connect(lambda: self.visual_controller.sync_customers(self.sim_manager.customers_model))

        # Map & Files
        self.view.map_combo.currentTextChanged.connect(self.load_map)
        self.view.btn_new_map.clicked.connect(self.create_new_map)
        self.view.btn_save_map.clicked.connect(self.save_current_map)
        self.view.btn_delete_map.clicked.connect(self.delete_current_map)
        self.view.btn_set_background.clicked.connect(self.select_map_background)
        self.view.btn_remove_background.clicked.connect(self.remove_map_background)
        self.view.spin_bg_scale.valueChanged.connect(self.visual_controller.update_bg_scale)
        self.view.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Tools (via InteractionController)
        ic = self.interaction_controller
        self.view.new_route_button.clicked.connect(lambda: ic.set_tool("route", button_ref=self.view.new_route_button))
        self.view.place_shelves_button.clicked.connect(lambda: ic.set_tool("shelf", button_ref=self.view.place_shelves_button))
        self.view.waiting_area_button.clicked.connect(lambda: ic.set_tool("waiting_area", button_ref=self.view.waiting_area_button))
        self.view.start_area_button.clicked.connect(lambda: ic.set_tool("start_area", button_ref=self.view.start_area_button))
        self.view.btn_start_route.clicked.connect(lambda: ic.set_tool("start_route", button_ref=self.view.btn_start_route))
        self.view.btn_exit_route.clicked.connect(lambda: ic.set_tool("exit_route", button_ref=self.view.btn_exit_route))
        self.view.btn_exit_area.clicked.connect(lambda: ic.set_tool("exit_area", button_ref=self.view.btn_exit_area))
        
        self.view.btn_kl.clicked.connect(lambda: ic.set_tool("checkout", {"type":"Normal", "ori":"Left"}, self.view.btn_kl))
        self.view.btn_kr.clicked.connect(lambda: ic.set_tool("checkout", {"type":"Normal", "ori":"Right"}, self.view.btn_kr))
        self.view.btn_sl.clicked.connect(lambda: ic.set_tool("checkout", {"type":"SB", "ori":"Left"}, self.view.btn_sl))
        self.view.btn_sr.clicked.connect(lambda: ic.set_tool("checkout", {"type":"SB", "ori":"Right"}, self.view.btn_sr))
        
        self.view.btn_save_admin.clicked.connect(ic.finish_route_drawing)
        self.view.btn_cancel_route.clicked.connect(ic.cancel_route_drawing)
        
        # Lists & Selection
        self.view.object_list_widget.itemClicked.connect(self.on_object_list_clicked)
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.btn_edit_obj.clicked.connect(lambda: ic.edit_object_position(self.selected_object_spec))
        self.view.btn_del_obj.clicked.connect(self.delete_selected_object)
        
        # Dialogs
        self.view.btn_visibility.clicked.connect(self.open_visibility_dialog)
        self.view.btn_offsets.clicked.connect(self.open_offsets_dialog)
        self.view.btn_config_sizes.clicked.connect(self.open_size_config_dialog)

    def toggle_play_pause(self):
        if self.sim_manager.is_running:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self.view.btn_play_pause.setText("▶")
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.map_manager.shop_routes:
            QMessageBox.warning(self.view, "Warnung", "Keine Shop-Routen!")
            self.view.btn_play_pause.setChecked(False)
            return
        if self.view.is_admin_mode:
            QMessageBox.warning(self.view, "Modus", "Bitte wechseln Sie in den Simulations-Modus.")
            self.view.btn_play_pause.setChecked(False)
            return
        
        if not self.sim_manager.is_initialized:
             self.sim_manager.init_day(
                 self.view.actor_count_input.value(), self.view.disabled_prob_input.value(),
                 self.view.time_open.time(), self.view.time_close.time()
             )
             self.visual_controller.draw_map_elements(self.map_manager)
        
        self.sim_manager.start()
        self.view.btn_play_pause.setChecked(True)
        self.view.btn_play_pause.setText("⏸")
        self._disable_inputs(True)

    def reset_simulation(self):
        self.sim_manager.reset(self.view.time_open.time())
        self.visual_controller.sync_customers([]) 
        self.view.btn_play_pause.setChecked(False)
        self.view.btn_play_pause.setText("▶")
        self._disable_inputs(False)
        self.view.list_log.clear()

    def _disable_inputs(self, disabled):
        self.view.time_open.setEnabled(not disabled)
        self.view.time_close.setEnabled(not disabled)
        self.view.actor_count_input.setEnabled(not disabled)
        self.view.disabled_prob_input.setEnabled(not disabled)

    def on_mode_changed(self, mode_text):
        self.view.update_sidebar_mode(mode_text)
        self.view.is_admin_mode = (mode_text == "Editor")
        if mode_text == "Editor" and self.sim_manager.is_running:
            self.toggle_play_pause()
        elif mode_text != "Editor":
            self.interaction_controller.set_tool(None)
        self.visual_controller.draw_map_elements(self.map_manager, self.selected_object_spec)

    def load_map(self, map_name):
        if not map_name: return
        
        if not map_name.lower().endswith(".json"):
            map_name += ".json"
            
        success, exit_dir = self.map_manager.load_map(map_name)
        if success:
            self.view.combo_global_exit.setCurrentText(exit_dir)
            self.view.spin_bg_scale.blockSignals(True)
            self.view.spin_bg_scale.setValue(self.map_manager.background_scale)
            self.view.spin_bg_scale.blockSignals(False)
            self.visual_controller.update_background(self.map_manager.background_image_path, self.map_manager.background_scale, MAPS_DIR)
            self.update_object_list()
            self.visual_controller.draw_map_elements(self.map_manager)

    def save_current_map(self):
        if self.map_manager.save_map(self.view.combo_global_exit.currentText()):
             QMessageBox.information(self.view, "Info", "Gespeichert.")

    def create_new_map(self):
        name, ok = QInputDialog.getText(self.view, "Neue Map", "Name (ohne .json):")
        if ok and name:
            new_name = self.map_manager.create_new_map(name)
            if new_name:
                self._refresh_map_list()
                display_name = new_name.replace(".json", "")
                self.view.map_combo.setCurrentText(display_name)

    def delete_current_map(self):
        if QMessageBox.question(self.view, "Löschen", "Wirklich löschen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.map_manager.delete_current_map(): self._refresh_map_list()

    def select_map_background(self):
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Hintergrundbild", str(IMAGE_DIR), "Bilder (*.png *.jpg *.jpeg)")
        if file_path:
            if self.map_manager.set_background(file_path):
                self.save_current_map()
                self.load_map(self.map_manager.current_map_file.name)

    def remove_map_background(self):
        self.map_manager.background_image_path = None
        self.visual_controller.update_background(None, 1.0, MAPS_DIR)
        self.save_current_map()

    def _refresh_map_list(self):
        self.view.map_combo.blockSignals(True)
        self.view.map_combo.clear()
        
        maps = self.map_manager.get_available_maps()
        
        preferred_map = "Standard (Einfach).json"
        current = self.map_manager.current_map_file
        target_file = current.name if current else preferred_map
        
        for m in maps:
            display_name = m.replace(".json", "")
            self.view.map_combo.addItem(display_name, m) 
            
        target_display = target_file.replace(".json", "")
        index = self.view.map_combo.findText(target_display)
        
        if index != -1:
            self.view.map_combo.setCurrentIndex(index)
        elif self.view.map_combo.count() > 0:
            self.view.map_combo.setCurrentIndex(0)
            
        self.view.map_combo.blockSignals(False)
        
        if not self.map_manager.current_map_file:
             self.load_map(self.view.map_combo.currentText())

    def update_object_list(self):
        self.view.route_list_widget.clear()
        for r in self.map_manager.shop_routes: self.view.route_list_widget.addItem(r)
        for r in self.map_manager.start_routes: self.view.route_list_widget.addItem(r)
        for r in self.map_manager.exit_routes: self.view.route_list_widget.addItem(r)

        self.view.object_list_widget.clear()
        for c in self.map_manager.checkouts_data:
            item = QListWidgetItem(f"Kasse #{c['id']} ({c['type']})")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "checkout", "id": c["id"]})
            self.view.object_list_widget.addItem(item)
        for idx, p in enumerate(self.map_manager.all_shelves):
            item = QListWidgetItem(f"Regal #{idx+1}")
            item.setData(Qt.ItemDataRole.UserRole, {"type": "shelf", "index": idx})
            self.view.object_list_widget.addItem(item)

    def on_object_list_clicked(self, item):
        self.selected_object_spec = item.data(Qt.ItemDataRole.UserRole)
        self.visual_controller.draw_map_elements(self.map_manager, self.selected_object_spec)

    def delete_selected_route(self):
        item = self.view.route_list_widget.currentItem()
        if not item: return
        name = item.text()
        if name in self.map_manager.shop_routes: del self.map_manager.shop_routes[name]
        elif name in self.map_manager.start_routes: del self.map_manager.start_routes[name]
        elif name in self.map_manager.exit_routes: del self.map_manager.exit_routes[name]
        self.view.route_list_widget.takeItem(self.view.route_list_widget.row(item))
        self.visual_controller.draw_map_elements(self.map_manager)

    def delete_selected_object(self):
        self.interaction_controller.delete_object(self.selected_object_spec)
        self.selected_object_spec = None
        self.update_object_list()

    def open_visibility_dialog(self):
        dlg = VisibilityDialog(self.settings, self.view)
        dlg.settings_changed.connect(lambda ns: (self.settings.update(ns), self.visual_controller.draw_map_elements(self.map_manager)))
        dlg.exec()
        self._save_settings()

    def open_offsets_dialog(self):
        self.visual_controller.draw_map_elements(self.map_manager, highlight_queues=True)
        dlg = OffsetDialog(self.settings, self.view)
        dlg.settings_changed.connect(lambda ns: (self.settings.update(ns), self.visual_controller.draw_map_elements(self.map_manager, highlight_queues=True)))
        dlg.exec()
        self._save_settings()
        self.visual_controller.draw_map_elements(self.map_manager, highlight_queues=False)

    def open_size_config_dialog(self):
        dlg = SizeConfigDialog(self.settings, self.view)
        dlg.settings_changed.connect(lambda ns: (self.settings.update(ns), self.visual_controller.draw_map_elements(self.map_manager)))
        dlg.exec()
        self._save_settings()

    def _save_settings(self):
        import json
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def _get_sim_params_from_ui(self, is_disabled):
        try:
            scan = (self.view.scan_speed_disabled_min.value(), self.view.scan_speed_disabled_max.value()) if is_disabled else \
                   (self.view.scan_speed_normal_min.value(), self.view.scan_speed_normal_max.value())
            return {
                "walk": (self.view.speed_walk_mean.value(), self.view.speed_walk_std.value()),
                "roll": (self.view.speed_roll_mean.value(), self.view.speed_roll_std.value()),
                "items": (self.view.items_mean.value(), self.view.items_std.value()),
                "scan": scan
            }
        except: return None