"""
Main Controller.
Refactored:
- FIX: 'load_map' now centers camera on the shop again (as requested),
       while Canvas handles the correct zoom level (1.0).
"""

from PyQt6.QtWidgets import (
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QListWidgetItem,
    QGraphicsView,
)
from PyQt6.QtCore import Qt

from config import (
    DEFAULT_SETTINGS,
    DEFAULT_LANGUAGE,
    SETTINGS_FILE,
    MAPS_DIR,
    IMAGE_DIR,
    FACTOR_1X,
    FACTOR_2X,
    FACTOR_4X,
    FACTOR_8X,
    FACTOR_16X,
    FACTOR_32X,
)
from i18n import TranslationManager
from controllers.map_manager import MapManager
from controllers.simulation_manager import SimulationManager
from controllers.visual_controller import VisualController
from controllers.interaction_controller import InteractionController
from views.main_window import MainWindow
from views.size_config_dialog import SizeConfigDialog
from views.dialogs import VisibilityDialog, OffsetDialog


class MainController:
    def __init__(self, translator=None):
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings_file = SETTINGS_FILE
        self._load_settings()

        # Use provided translator or create new one
        if translator:
            self.translator = translator
        else:
            language = self.settings.get("language", DEFAULT_LANGUAGE)
            self.translator = TranslationManager(language)

        self.view = MainWindow(translator=self.translator)
        self.view.set_controller(self)

        self.map_manager = MapManager(self.settings)
        self.sim_manager = SimulationManager(self.map_manager, self.settings)
        self.visual_controller = VisualController(
            self.view.sim_scene, self.settings, translator=self.translator
        )

        self.interaction_controller = InteractionController(
            self.view.sim_scene,
            self.map_manager,
            self.visual_controller,
            self.view,
            self.sim_manager,
        )

        self._setup_connections()
        self._init_ui_state()

        self.load_map("Standard (Einfach).json")
        self.view.showMaximized()

    def _setup_connections(self):
        # Language change
        self.view.sidebar_component.language_changed.connect(self.on_language_changed)
        
        self.view.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        self.view.btn_play_pause.clicked.connect(self.toggle_simulation)
        self.view.btn_reset.clicked.connect(self.reset_simulation)
        self.view.btn_skip.clicked.connect(self.skip_day)

        self.view.btn_speed_1.clicked.connect(
            lambda: self.set_speed(FACTOR_1X)
        )
        self.view.btn_speed_2.clicked.connect(
            lambda: self.set_speed(FACTOR_4X)
        )
        self.view.btn_speed_3.clicked.connect(
            lambda: self.set_speed(FACTOR_16X)
        )

        # Reset Zoom mit Center-Berechnung
        self.view.btn_reset_zoom.clicked.connect(
            lambda: self.view.reset_sim_zoom(
                self.visual_controller.get_map_center()
            )
        )

        self.sim_manager.time_updated.connect(self._update_clock_ui)
        self.sim_manager.stats_updated.connect(
            lambda w, c, t: (
                self.view.lbl_queue_count.setText(str(w)),
                self.view.lbl_customers_in_store.setText(str(c)),
                self.view.lbl_total_customers.setText(str(t)),
                self._check_overtime(c),
            )
        )
        self.sim_manager.log_message.connect(self.view.add_log_entry)
        self.sim_manager.day_finished.connect(self._on_day_finished)
        self.sim_manager.sim_timer.timeout.connect(self._on_sim_tick)

        self.view.map_combo.currentTextChanged.connect(self.load_map)
        self.view.btn_new_map.clicked.connect(self.create_new_map)
        self.view.btn_save_map.clicked.connect(self.save_current_map)
        self.view.btn_delete_map.clicked.connect(self.delete_current_map)
        self.view.btn_set_background.clicked.connect(
            self.select_map_background
        )
        self.view.btn_remove_background.clicked.connect(
            self.remove_map_background
        )
        self.view.spin_bg_scale.valueChanged.connect(self.update_bg_scale)

        self.view.btn_config_sizes.clicked.connect(self.open_size_config)
        self.view.btn_offsets.clicked.connect(self.open_offsets_dialog)
        self.view.btn_visibility.clicked.connect(self.open_visibility_dialog)

        self.interaction_controller.map_data_changed.connect(
            self.on_map_data_changed
        )
        self.visual_controller.set_checkout_click_callback(
            self.on_checkout_clicked
        )
        self.visual_controller.set_shelf_click_callback(self.on_shelf_clicked)

        ic = self.interaction_controller
        self.view.start_area_button.clicked.connect(
            lambda: ic.set_tool(
                "start_area", button_ref=self.view.start_area_button
            )
        )
        self.view.waiting_area_button.clicked.connect(
            lambda: ic.set_tool(
                "waiting_area", button_ref=self.view.waiting_area_button
            )
        )
        self.view.btn_exit_area.clicked.connect(
            lambda: ic.set_tool(
                "exit_area", button_ref=self.view.btn_exit_area
            )
        )
        self.view.btn_start_route.clicked.connect(
            lambda: ic.set_tool(
                "start_route", button_ref=self.view.btn_start_route
            )
        )
        self.view.btn_exit_route.clicked.connect(
            lambda: ic.set_tool(
                "exit_route", button_ref=self.view.btn_exit_route
            )
        )
        self.view.new_route_button.clicked.connect(
            lambda: ic.set_tool("route", button_ref=self.view.new_route_button)
        )
        self.view.place_shelves_button.clicked.connect(
            lambda: ic.set_tool(
                "shelf", button_ref=self.view.place_shelves_button
            )
        )

        self.view.btn_kl.clicked.connect(
            lambda: ic.set_tool(
                "checkout", {"type": "Normal", "ori": "Left"}, self.view.btn_kl
            )
        )
        self.view.btn_kr.clicked.connect(
            lambda: ic.set_tool(
                "checkout",
                {"type": "Normal", "ori": "Right"},
                self.view.btn_kr,
            )
        )
        self.view.btn_sl.clicked.connect(
            lambda: ic.set_tool(
                "checkout", {"type": "SB", "ori": "Left"}, self.view.btn_sl
            )
        )
        self.view.btn_sr.clicked.connect(
            lambda: ic.set_tool(
                "checkout", {"type": "SB", "ori": "Right"}, self.view.btn_sr
            )
        )
        self.view.btn_move_map.clicked.connect(
            lambda: ic.set_tool("move_map", button_ref=self.view.btn_move_map)
        )

        self.view.btn_save_admin.clicked.connect(ic.finish_route_drawing)
        self.view.btn_cancel_route.clicked.connect(ic.cancel_route_drawing)
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.route_list_widget.itemClicked.connect(self.on_route_selected)
        self.view.btn_del_obj.clicked.connect(self.delete_selected_object)
        self.view.btn_edit_obj.clicked.connect(self.edit_selected_object)
        self.view.object_list_widget.itemClicked.connect(
            self.on_object_selected
        )

    def _update_clock_ui(self, time_str):
        self.view.clock_widget.setText(time_str)
        current = self.sim_manager.sim_time
        open_t = self.sim_manager.open_time
        close_t = self.sim_manager.close_time
        total_secs = open_t.secsTo(close_t)
        elapsed = open_t.secsTo(current)
        if total_secs > 0:
            progress = elapsed / total_secs
            self.view.clock_widget.set_progress(progress)
        is_past_closing = elapsed >= total_secs
        if not is_past_closing:
            self.view.clock_widget.set_overtime(False)

    def _check_overtime(self, customers_in_store):
        current = self.sim_manager.sim_time
        close_t = self.sim_manager.close_time
        if current >= close_t and customers_in_store > 0:
            self.view.clock_widget.set_overtime(True)
        else:
            self.view.clock_widget.set_overtime(False)

    def _on_sim_tick(self):
        self.visual_controller.sync_all_agents(
            self.sim_manager.customers_model, []
        )
        self.visual_controller.update_checkout_status(
            self.map_manager.checkouts_data
        )

    def _on_day_finished(self):
        QMessageBox.information(self.view, "Info", "Tag beendet.")
        self.view.btn_play_pause.setChecked(False)
        self.view.btn_play_pause.setText("▶")
        self.view.clock_widget.set_overtime(False)

    def _init_ui_state(self):
        self._refresh_map_list()
        self.on_mode_changed("Simulation")
        self.sim_manager.time_updated.emit(
            self.sim_manager.sim_time.toString("HH:mm")
        )
        self.sim_manager.set_param_accessor(self._get_sim_params_from_ui)

    def show(self):
        self.view.showMaximized()

    def _load_settings(self):
        if self.settings_file.exists():
            import json

            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))

    def _save_settings(self):
        import json

        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def open_size_config(self):
        dlg = SizeConfigDialog(self.settings, self.view)
        if dlg.exec():
            self.settings.update(dlg.get_values())
            self._save_settings()
            self.visual_controller.draw_map_elements(self.map_manager)

    def open_offsets_dialog(self):
        self.visual_controller.draw_map_elements(
            self.map_manager, highlight_queues=True
        )
        dlg = OffsetDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (
                self.settings.update(ns),
                self.visual_controller.draw_map_elements(
                    self.map_manager, highlight_queues=True
                ),
            )
        )
        dlg.exec()
        self._save_settings()
        self.visual_controller.draw_map_elements(
            self.map_manager, highlight_queues=False
        )

    def open_visibility_dialog(self):
        dlg = VisibilityDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (
                self.settings.update(ns),
                self.visual_controller.draw_map_elements(self.map_manager),
            )
        )
        dlg.exec()
        self._save_settings()

    def _refresh_map_list(self):
        self.view.map_combo.blockSignals(True)
        self.view.map_combo.clear()
        maps = self.map_manager.get_available_maps()
        self.view.map_combo.addItems(maps)

        preferred_map = "Standard (Einfach).json"
        target = None
        if self.map_manager.current_map_file:
            target = self.map_manager.current_map_file.name
        if not target and preferred_map in maps:
            target = preferred_map
        if target:
            index = self.view.map_combo.findText(target)
            if index != -1:
                self.view.map_combo.setCurrentIndex(index)
            else:
                self.view.map_combo.setCurrentIndex(0)
        elif self.view.map_combo.count() > 0:
            self.view.map_combo.setCurrentIndex(0)
        self.view.map_combo.blockSignals(False)

    def on_mode_changed(self, mode_text):
        self.view.update_sidebar_mode(mode_text)
        self.view.is_admin_mode = mode_text == "Editor"
        if mode_text == "Simulation":
            self.interaction_controller.set_tool(None)
            self.view.canvas_component.set_drawing_cursor(False)
            self.view.btn_reset.setEnabled(True)
            if self.sim_manager.is_running:
                self.view.btn_play_pause.setChecked(True)
                self.view.btn_play_pause.setText("⏸")
            else:
                self.view.btn_play_pause.setChecked(False)
                self.view.btn_play_pause.setText("▶")
        else:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self.view.btn_play_pause.setText("▶")
            self.view.canvas_component.set_drawing_cursor(True)
        self.visual_controller.draw_map_elements(self.map_manager)

    def on_map_data_changed(self):
        self._refresh_route_list()
        self._refresh_object_list()

    def create_new_map(self):
        name, ok = QInputDialog.getText(
            self.view, "Neue Karte", "Name der Karte (ohne .json):"
        )
        if ok and name:
            if not name.endswith(".json"):
                name += ".json"
            self.map_manager.reset_map()
            self.map_manager.create_new_map(name)
            self.map_manager.current_map_file = MAPS_DIR / name
            self.map_manager.save_map()
            self._refresh_map_list()
            self.view.map_combo.setCurrentText(name)
            self.visual_controller.draw_map_elements(self.map_manager)
            self.view.add_log_entry(f"Karte '{name}' erstellt.", "green")

    def load_map(self, filename):
        if not filename:
            return
        if self.map_manager.load_map(filename):
            self.visual_controller.update_background(
                self.map_manager.background_image_path,
                self.map_manager.background_scale,
                MAPS_DIR,
            )
            self.view.spin_bg_scale.setValue(self.map_manager.background_scale)
            self.visual_controller.draw_map_elements(self.map_manager)
            self._refresh_object_list()
            self._refresh_route_list()

            # WICHTIG: Hier wieder mit Center aufrufen für "Näher beim Start"
            center = self.visual_controller.get_map_center()
            self.view.reset_sim_zoom(center)

    def save_current_map(self):
        if self.map_manager.save_map(
            self.view.combo_global_exit.currentText()
        ):
            self.view.add_log_entry(f"Karte gespeichert.", "green")
            QMessageBox.information(
                self.view, "Info", "Karte erfolgreich gespeichert."
            )
        else:
            QMessageBox.warning(
                self.view, "Fehler", "Speichern fehlgeschlagen."
            )

    def delete_current_map(self):
        res = QMessageBox.question(
            self.view,
            "Löschen",
            "Karte wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if res == QMessageBox.StandardButton.Yes:
            if self.map_manager.delete_current_map():
                self.view.add_log_entry("Karte gelöscht.", "red")
                self._refresh_map_list()
                if self.view.map_combo.count() > 0:
                    self.load_map(self.view.map_combo.itemText(0))
                else:
                    self.visual_controller.draw_map_elements(self.map_manager)
            else:
                QMessageBox.warning(
                    self.view, "Fehler", "Konnte Karte nicht löschen."
                )

    def select_map_background(self):
        path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Hintergrund wählen",
            str(MAPS_DIR),
            "Images (*.png *.jpg)",
        )
        if path:
            self.map_manager.set_background(path)
            self.map_manager.save_map()
            self.visual_controller.update_background(
                self.map_manager.background_image_path,
                self.map_manager.background_scale,
                MAPS_DIR,
            )

    def remove_map_background(self):
        self.map_manager.background_image_path = None
        self.map_manager.save_map()
        self.visual_controller.update_background(None, 1.0, MAPS_DIR)

    def update_bg_scale(self, val):
        self.map_manager.background_scale = val
        self.visual_controller.update_bg_scale(val)

    def toggle_simulation(self):
        if self.sim_manager.is_running:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self.view.btn_play_pause.setText("▶")
        else:
            if not self.sim_manager.is_initialized:
                try:
                    count = self.view.actor_count_input.value()
                    prob = self.view.disabled_prob_input.value()
                    ot = self.view.time_open.time()
                    ct = self.view.time_close.time()
                    self.sim_manager.init_day(count, prob, ot, ct)
                except Exception as e:
                    QMessageBox.warning(
                        self.view, "Fehler", f"Ungültige Parameter: {e}"
                    )
                    self.view.btn_play_pause.setChecked(False)
                    return
            self.sim_manager.start()
            self.view.btn_play_pause.setChecked(True)
            self.view.btn_play_pause.setText("⏸")

    def reset_simulation(self):
        ot = self.view.time_open.time()
        self.sim_manager.reset(ot)
        self.view.btn_play_pause.setChecked(False)
        self.view.btn_play_pause.setText("▶")
        self.view.clock_widget.set_progress(0)
        self.view.clock_widget.set_overtime(False)
        self.visual_controller.sync_customers([])
        self.visual_controller.draw_map_elements(self.map_manager)

        # Reset View auch hier
        center = self.visual_controller.get_map_center()
        self.view.reset_sim_zoom(center)

    def skip_day(self):
        if self.sim_manager.is_initialized:
            self.sim_manager.skip_day()
            self.view.btn_play_pause.setChecked(False)
            self.view.btn_play_pause.setText("▶")

    def set_speed(self, factor):
        self.sim_manager.set_time_factor(factor)

    def _get_sim_params_from_ui(self, is_disabled):
        try:
            handheld_val = 0
            if hasattr(self.view, "hand_scanner_prob"):
                handheld_val = self.view.hand_scanner_prob.value()
            scan = (
                (
                    self.view.scan_speed_disabled_min.value(),
                    self.view.scan_speed_disabled_max.value(),
                )
                if is_disabled
                else (
                    self.view.scan_speed_normal_min.value(),
                    self.view.scan_speed_normal_max.value(),
                )
            )
            staff = {
                "newbie": (
                    self.view.scan_speed_newbie_min.value(),
                    self.view.scan_speed_newbie_max.value(),
                ),
                "pro": (
                    self.view.scan_speed_pro_min.value(),
                    self.view.scan_speed_pro_max.value(),
                ),
            }
            fail_rate_normal = 0.0
            if hasattr(self.view, "checkout_fail_rate_normal"):
                fail_rate_normal = self.view.checkout_fail_rate_normal.value()
            fail_rate_sb = 0.0
            if hasattr(self.view, "checkout_fail_rate_sb"):
                fail_rate_sb = self.view.checkout_fail_rate_sb.value()
            customer_annoyance_rate = 0.0
            if hasattr(self.view, "customer_annoyance_rate"):
                customer_annoyance_rate = self.view.customer_annoyance_rate.value()
            return {
                "walk": (
                    self.view.speed_walk_mean.value(),
                    self.view.speed_walk_std.value(),
                ),
                "roll": (
                    self.view.speed_roll_mean.value(),
                    self.view.speed_roll_std.value(),
                ),
                "items": (
                    self.view.items_mean.value(),
                    self.view.items_std.value(),
                ),
                "scan": scan,
                "staff": staff,
                "handheld": handheld_val,
                "checkout_fail_rate_normal": fail_rate_normal,
                "checkout_fail_rate_sb": fail_rate_sb,
                "customer_annoyance_rate": customer_annoyance_rate,
            }
        except Exception as e:
            print(f"UI Params Error: {e}")
            return None

    # Proxies omitted for brevity (same as previous) but need to be in final file.
    # Just copying methods from previous response for completion:
    def on_checkout_clicked(self, cid):
        self.interaction_controller.handle_checkout_click(cid)
        self._highlight_list_item(self.view.object_list_widget, cid)

    def on_shelf_clicked(self, idx):
        self.interaction_controller.handle_shelf_click(idx)
        self._highlight_list_item(self.view.object_list_widget, idx)

    def on_route_selected(self, item):
        name = item.text().split(" ")[0]

    def on_object_selected(self, item):
        spec = item.data(Qt.ItemDataRole.UserRole)
        self.interaction_controller.edit_object_position(spec)

    def delete_selected_route(self):
        self._refresh_route_list()

    def delete_selected_object(self):
        item = self.view.object_list_widget.currentItem()
        if item:
            self.interaction_controller.delete_object(
                item.data(Qt.ItemDataRole.UserRole)
            )
            self.visual_controller.draw_map_elements(self.map_manager)
            self._refresh_object_list()

    def edit_selected_object(self):
        item = self.view.object_list_widget.currentItem()
        if item:
            spec = item.data(Qt.ItemDataRole.UserRole)
            self.interaction_controller.edit_object_position(spec)
        self.visual_controller.draw_map_elements(self.map_manager)

    def _refresh_route_list(self):
        self.view.route_list_widget.clear()
        for name, pts in self.map_manager.shop_routes.items():
            self.view.route_list_widget.addItem(f"{name} ({len(pts)} Pkt)")
        for name, pts in self.map_manager.start_routes.items():
            self.view.route_list_widget.addItem(f"{name} (Start)")
        for name, pts in self.map_manager.exit_routes.items():
            self.view.route_list_widget.addItem(f"{name} (Exit)")

    def _refresh_object_list(self):
        self.view.object_list_widget.clear()
        for i, s in enumerate(self.map_manager.all_shelves):
            item = QListWidgetItem(f"Regal #{i} ({s.get('variant',0)})")
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "shelf", "index": i}
            )
            self.view.object_list_widget.addItem(item)
        for c in self.map_manager.checkouts_data:
            item = QListWidgetItem(f"Kasse #{c['id']} ({c['type']})")
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "checkout", "id": c["id"]}
            )
            self.view.object_list_widget.addItem(item)

    def _highlight_list_item(self, list_widget, ID_val):
        for i in range(list_widget.count()):
            it = list_widget.item(i)
            if f"#{ID_val}" in it.text():
                it.setSelected(True)

    def on_language_changed(self, language: str):
        """Handle language change from UI - rebuilds entire sidebar for complete refresh."""
        # Pause simulation to avoid accessing deleted UI widgets
        was_running = self.sim_manager.is_running
        if was_running:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self.view.btn_play_pause.setText("▶")
        
        self.translator.set_language(language)
        self.settings["language"] = language
        self._save_settings()
        
        # Refresh toolbar (simple text updates)
        self.view.toolbar_component.refresh_translations(self.translator)
        
        # Rebuild entire sidebar to ensure ALL widgets (including lazy-loaded tabs) are created with correct translations
        self.view.rebuild_sidebar(self.translator)
        
        # Refresh checkout displays with new translations
        self.visual_controller.refresh_checkout_displays(self.translator)
        
        # Update window title
        self.view.setWindowTitle(self.translator.get("window.title"))
        
        # Reconnect param accessor to ensure simulation can access new UI elements
        self.sim_manager.set_param_accessor(self._get_sim_params_from_ui)
        
        # Resume simulation if it was running
        if was_running:
            self.sim_manager.start()
            self.view.btn_play_pause.setChecked(True)
            self.view.btn_play_pause.setText("⏸")
