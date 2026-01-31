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
    QStyle,
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
from views.statistics_dialogs import StatisticsReportDialog


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
        
        # Give sidebar access to controller, map_manager and visual_controller
        self.view.sidebar_component.controller = self
        self.view.sidebar_component.map_manager = self.map_manager
        self.view.sidebar_component.visual_controller = self.visual_controller

        self.interaction_controller = InteractionController(
            self.view.sim_scene,
            self.map_manager,
            self.visual_controller,
            self.view,
            self.sim_manager,
        )

        self.stats_dialog = None
        self.settings["show_checkout_numbers"] = False

        self._setup_connections()
        self._init_ui_state()

        # Preload customer images to avoid lag on first customer spawn
        self._preload_customer_images()

        self.load_map("Standard 1.json")
        self.view.showMaximized()

    def _setup_connections(self):
        # Back to main menu
        self.view.sidebar_component.back_to_menu_requested.connect(
            self.on_back_to_menu
        )

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
            lambda: self.view.reset_sim_zoom()
        )

        self.sim_manager.time_updated.connect(self._update_clock_ui)
        self.sim_manager.stats_updated.connect(self._on_stats_updated)
        self.sim_manager.live_stats_updated.connect(
            self._on_live_stats_updated
        )
        self.sim_manager.stats_ready.connect(self._on_stats_ready)
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
        self.view.btn_open_report.clicked.connect(self._open_stats_report)

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

        self.view.btn_checkout_normal.clicked.connect(
            lambda: ic.set_tool(
                "checkout",
                {"type": "Normal"},
                self.view.btn_checkout_normal,
            )
        )
        self.view.btn_checkout_sb.clicked.connect(
            lambda: ic.set_tool(
                "checkout", {"type": "SB"}, self.view.btn_checkout_sb
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

    def _on_stats_updated(self, queue_count, customers_in_store, total_customers):
        """Handle basic stats update signal (backwards compatibility)."""
        sb = self.view.sidebar_component
        if hasattr(sb, 'lbl_queue_count'):
            sb.lbl_queue_count.setText(str(queue_count))
        if hasattr(sb, 'lbl_customers_in_store'):
            sb.lbl_customers_in_store.setText(str(customers_in_store))
        # Note: total_customers from this signal is total_spawned, not served
        # For "Gesamt bedient" we use live_stats_updated which has total_customers_served
        self._check_overtime(customers_in_store)

    def _update_clock_ui(self, time_str):
        self.view.clock_widget.setText(time_str)
        current = self.sim_manager.sim_time
        total_secs = self.sim_manager.get_open_duration_seconds()
        elapsed = self.sim_manager.get_elapsed_open_seconds(current)
        if total_secs > 0:
            progress = elapsed / total_secs
            self.view.clock_widget.set_progress(progress)
        if not self.sim_manager.store_is_closed_trigger:
            self.view.clock_widget.set_overtime(False)

    def _on_live_stats_updated(self, stats):
        """Update all statistics widgets with live data using StatsUpdater."""
        # Quick alias for sidebar component
        sb = self.view.sidebar_component
        
        # Use StatsUpdater for clean, thematic updates
        if hasattr(sb, 'stats_updater'):
            sb.stats_updater.update_all(stats)
        else:
            # Fallback to old method if stats_updater not available
            self._update_stats_legacy(stats)
        
        # Check overtime status
        customers_in_store = stats.get("customers_in_store", 0)
        self._check_overtime(customers_in_store)
    
    def _update_stats_legacy(self, stats):
        """Legacy method for updating stats (fallback)."""
        sb = self.view.sidebar_component
        
        # Update queue count in live tab
        queue_count = stats.get("queue_count", 0)
        if hasattr(sb, 'lbl_queue_count'):
            sb.lbl_queue_count.setText(str(queue_count))
        
        # Update customers in store
        customers_in_store = stats.get("customers_in_store", 0)
        if hasattr(sb, 'lbl_customers_in_store'):
            sb.lbl_customers_in_store.setText(str(customers_in_store))
        
        # Update total customers SERVED (Live tab: "Gesamt bedient")
        total_customers_served = stats.get("total_customers_served", 0)
        if hasattr(sb, 'lbl_total_customers_served_live'):
            sb.lbl_total_customers_served_live.setText(str(total_customers_served))
        
        # Update total customers SERVED (Details tab: "HEUTE BEDIENT")
        if hasattr(sb, 'lbl_total_customers'):
            sb.lbl_total_customers.setText(str(total_customers_served))
        
        # Longest queue
        max_len = stats.get("longest_queue", 0)
        checkout_ids = stats.get("longest_queue_checkouts", [])
        if max_len > 0 and checkout_ids:
            ids_text = ", ".join(str(cid) for cid in checkout_ids)
            if hasattr(sb, 'lbl_longest_queue'):
                sb.lbl_longest_queue.setText(f"Kasse #{ids_text} ({max_len})")
        else:
            if hasattr(sb, 'lbl_longest_queue'):
                sb.lbl_longest_queue.setText(f"Kasse #0 ({max_len})")
        
        # Average wait time
        avg_wait = stats.get("avg_wait_time_min", 0.0)
        if hasattr(sb, 'lbl_avg_wait'):
            sb.lbl_avg_wait.setText(f"{avg_wait:.1f} min")
        
        # Update wait time progress bar and status
        if hasattr(sb, 'wait_progress'):
            wait_value = min(int(avg_wait), 10)
            sb.wait_progress.setValue(wait_value)
            
            # Update progress bar color based on wait time
            if avg_wait <= 3:
                color = "#10B981"  # Green
            elif avg_wait <= 5:
                color = "#F59E0B"  # Orange
            else:
                color = "#EF4444"  # Red
            
            sb.wait_progress.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 3px;
                    background-color: #E5E7EB;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
        
        # Throughput
        throughput = stats.get("throughput_per_hour", 0.0)
        if hasattr(sb, 'lbl_throughput'):
            sb.lbl_throughput.setText(f"{throughput:.0f} Kunden/h")
        
        # Checkouts status
        open_c = stats.get("checkouts_open", 0)
        avail_c = stats.get("checkouts_available", 0)
        total_c = stats.get("total_checkouts", open_c)
        malfunction_c = stats.get("checkouts_malfunction", 0)
        closed_c = total_c - open_c
        
        if hasattr(sb, 'lbl_available_checkouts'):
            sb.lbl_available_checkouts.setText(f"{avail_c}/{open_c}")
        
        # Update new checkout status labels
        if hasattr(sb, 'lbl_checkouts_open'):
            sb.lbl_checkouts_open.setText(str(avail_c))
        if hasattr(sb, 'lbl_checkouts_malfunction'):
            sb.lbl_checkouts_malfunction.setText(str(malfunction_c))
        if hasattr(sb, 'lbl_checkouts_closed'):
            sb.lbl_checkouts_closed.setText(str(closed_c))
        
        # Satisfaction
        satisfaction = stats.get("satisfaction_score", 0.0)
        if hasattr(sb, 'lbl_satisfaction_score'):
            sb.lbl_satisfaction_score.setText(f"{satisfaction:.0f}%")
        
        # Update satisfaction progress and status
        if hasattr(sb, 'satisfaction_progress'):
            sb.satisfaction_progress.setValue(int(satisfaction))
            
            # Update progress bar color based on satisfaction
            if satisfaction >= 80:
                color = "#10B981"  # Green
            elif satisfaction >= 60:
                color = "#F59E0B"  # Orange
            else:
                color = "#EF4444"  # Red
            
            sb.satisfaction_progress.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 5px;
                    background-color: #E5E7EB;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 5px;
                }}
            """)
        
        if hasattr(sb, 'lbl_satisfaction_status'):
            if satisfaction >= 80:
                sb.lbl_satisfaction_status.setText("Status: SEHR GUT")
                sb.lbl_satisfaction_status.setStyleSheet("font-size: 13px; color: #10B981; font-weight: 700; text-align: center;")
            elif satisfaction >= 60:
                sb.lbl_satisfaction_status.setText("Status: GUT")
                sb.lbl_satisfaction_status.setStyleSheet("font-size: 13px; color: #F59E0B; font-weight: 700; text-align: center;")
            else:
                sb.lbl_satisfaction_status.setText("Status: KRITISCH")
                sb.lbl_satisfaction_status.setStyleSheet("font-size: 11px; color: #EF4444; font-weight: 700; text-align: center;")
        
        # Time tracking
        elapsed = stats.get("elapsed_open_seconds", 0.0)
        scheduled = stats.get("scheduled_open_seconds", 0.0)
        overtime = stats.get("overtime_seconds", 0.0)
        if hasattr(sb, 'lbl_elapsed_open'):
            sb.lbl_elapsed_open.setText(self._format_duration(elapsed))
        if hasattr(sb, 'lbl_scheduled_open'):
            sb.lbl_scheduled_open.setText(self._format_duration(scheduled))
        
        # Format overtime with sign
        if overtime > 0:
            if hasattr(sb, 'lbl_overtime'):
                sb.lbl_overtime.setText(f"+{self._format_duration(overtime)}")
        else:
            if hasattr(sb, 'lbl_overtime'):
                sb.lbl_overtime.setText(self._format_duration(0))
        
        # Details Tab: Article statistics
        if hasattr(sb, 'lbl_total_items'):
            total_items = stats.get("total_items_processed", 0)
            sb.lbl_total_items.setText(str(total_items))
        
        if hasattr(sb, 'lbl_avg_items_per_customer'):
            avg_items = stats.get("avg_items_per_customer", 0.0)
            sb.lbl_avg_items_per_customer.setText(f"{avg_items:.1f}")
        
        # Details Tab: Payment methods
        if hasattr(sb, 'lbl_payment_cash'):
            cash_percent = stats.get("payment_cash_percent", 0.0)
            sb.lbl_payment_cash.setText(f"{cash_percent:.0f}%")
        
        if hasattr(sb, 'lbl_payment_card'):
            card_percent = stats.get("payment_card_percent", 0.0)
            sb.lbl_payment_card.setText(f"{card_percent:.0f}%")
        
        # Details Tab: Problems (Störungen, Verärgerungen, Konflikte)
        if hasattr(sb, 'lbl_malfunctions'):
            malfunctions = stats.get("malfunctions_today", 0)
            sb.lbl_malfunctions.setText(str(malfunctions))
        
        if hasattr(sb, 'lbl_annoyance'):
            annoyance = stats.get("annoyance_today", 0)
            sb.lbl_annoyance.setText(str(annoyance))
        
        if hasattr(sb, 'lbl_conflicts'):
            conflicts = stats.get("conflicts_today", 0)
            sb.lbl_conflicts.setText(str(conflicts))

    def _format_duration(self, seconds):
        total = int(round(seconds))
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h}:{m:02d}"

    def _check_overtime(self, customers_in_store):
        if self.sim_manager.store_is_closed_trigger and customers_in_store > 0:
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
        self._set_play_pause_icon(False)
        self.view.clock_widget.set_overtime(False)

    def _on_stats_ready(self, stats):
        if self.stats_dialog and self.stats_dialog.isVisible():
            self.stats_dialog.raise_()
            self.stats_dialog.activateWindow()
            return
        dlg = StatisticsReportDialog(
            stats,
            parent=self.view,
            translator=self.translator,
            sim_manager=None,
            settings=self.settings,
        )
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._attach_report_checkout_ids(dlg)
        dlg.show()

    def _open_stats_report(self):
        if self.stats_dialog and self.stats_dialog.isVisible():
            self.stats_dialog.raise_()
            self.stats_dialog.activateWindow()
            return
        stats = self.sim_manager.get_statistics_snapshot()
        dlg = StatisticsReportDialog(
            stats,
            parent=self.view,
            translator=self.translator,
            sim_manager=self.sim_manager,
            settings=self.settings,
        )
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        dlg.show()
        self.stats_dialog = dlg
        self._attach_report_checkout_ids(dlg)
        dlg.destroyed.connect(lambda: setattr(self, "stats_dialog", None))

    def _attach_report_checkout_ids(self, dlg):
        self._set_checkout_numbers_visible(True)
        dlg.destroyed.connect(self._restore_report_checkout_ids)

    def _restore_report_checkout_ids(self):
        self._set_checkout_numbers_visible(False)

    def _set_checkout_numbers_visible(self, visible):
        self.settings["show_checkout_numbers"] = visible
        try:
            self.visual_controller.draw_map_elements(self.map_manager)
        except RuntimeError:
            return

    def _init_ui_state(self):
        self._refresh_map_list()
        self.on_mode_changed("Simulation")
        self.sim_manager.time_updated.emit(
            self.sim_manager.sim_time.toString("HH:mm")
        )
        self.sim_manager.set_param_accessor(self._get_sim_params_from_ui)

    def _preload_customer_images(self):
        """Preload customer images to avoid lag when first customer appears."""
        from views.items.customer_item import CustomerItem

        # Call class methods to load images into class variables
        CustomerItem._load_images()
        CustomerItem._load_icons()

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
        dlg = SizeConfigDialog(
            self.settings,
            self.view,
            translator=self.translator,
        )
        if dlg.exec():
            self.settings.update(dlg.get_values())
            self._save_settings()
            self.visual_controller.draw_map_elements(self.map_manager)

    def open_offsets_dialog(self):
        self.visual_controller.draw_map_elements(
            self.map_manager, highlight_queues=True
        )
        dlg = OffsetDialog(self.settings, self.view, translator=self.translator)
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
        dlg = VisibilityDialog(self.settings, self.view, translator=self.translator)
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

        # Filter and format map names
        display_maps = []
        for map_name in maps:
            # Skip default.json if there are other maps
            if map_name == "default.json" and len(maps) > 1:
                continue
            # Remove .json extension for display
            display_name = map_name.replace(".json", "")
            display_maps.append((display_name, map_name))  # (display, actual)

        # Add formatted names to combo
        for display_name, _ in display_maps:
            self.view.map_combo.addItem(display_name)

        preferred_map = "Standard 1.json"
        target = None
        if self.map_manager.current_map_file:
            target = self.map_manager.current_map_file.name
        if not target and preferred_map in maps:
            target = preferred_map

        # Find and select the target map
        if target:
            # Remove .json for comparison
            target_display = target.replace(".json", "")
            index = self.view.map_combo.findText(target_display)
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
                self._set_play_pause_icon(True)
            else:
                self.view.btn_play_pause.setChecked(False)
                self._set_play_pause_icon(False)
        else:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self._set_play_pause_icon(False)
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
            # Set combo to display name (without .json)
            display_name = name.replace(".json", "")
            self.view.map_combo.setCurrentText(display_name)
            self.visual_controller.draw_map_elements(self.map_manager)
            self._refresh_object_list()
            self._refresh_route_list()
            self.view.add_log_entry(f"Karte '{name}' erstellt.", "green")

    def load_map(self, filename):
        if not filename:
            return
        # Add .json extension if not present (combo now shows display names without .json)
        if not filename.endswith(".json"):
            filename = filename + ".json"
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
            self.view.reset_sim_zoom()

    def save_current_map(self):
        if self.map_manager.save_map():
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
        self.map_manager._apply_default_background()
        self.map_manager.save_map()
        self.visual_controller.update_background(
            self.map_manager.background_image_path,
            self.map_manager.background_scale,
            MAPS_DIR,
        )

    def update_bg_scale(self, val):
        self.map_manager.background_scale = val
        self.visual_controller.update_bg_scale(val)

    def toggle_simulation(self):
        if self.sim_manager.is_running:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self._set_play_pause_icon(False)
            # Input is still blocked during pause
        else:
            if not self.sim_manager.is_initialized:
                has_open_checkout = any(
                    c.get("open", True)
                    for c in self.map_manager.checkouts_data
                )
                if not has_open_checkout:
                    title = (
                        self.translator.get(
                            "errors.no_open_checkout_title", "Fehler"
                        )
                        if self.translator
                        else "Fehler"
                    )
                    message = (
                        self.translator.get(
                            "errors.no_open_checkout_message",
                            "Mindestens eine Kasse (Normal oder SB) muss geöffnet sein, um die Simulation zu starten.",
                        )
                        if self.translator
                        else "Mindestens eine Kasse (Normal oder SB) muss geöffnet sein, um die Simulation zu starten."
                    )
                    QMessageBox.warning(self.view, title, message)
                    self.view.btn_play_pause.setChecked(False)
                    return
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
            self._set_play_pause_icon(True)
            # Preload all input tabs before blocking
            self.view.sidebar_component.preload_all_input_tabs()
            # Block input when simulation starts
            self.view.sidebar_component.set_input_blocked(
                True, self.translator
            )
            # Switch to statistics tab when simulation starts
            self.view.sidebar_component.main_tabs.setCurrentIndex(1)

    def reset_simulation(self):
        ot = self.view.time_open.time()
        self.sim_manager.reset(ot)
        self.view.btn_play_pause.setChecked(False)
        self._set_play_pause_icon(False)
        self.view.clock_widget.set_progress(0)
        self.view.clock_widget.set_overtime(False)
        self.visual_controller.sync_customers([])
        self.visual_controller.draw_map_elements(self.map_manager)

        # Reset View auch hier
        self.view.reset_sim_zoom()

        # Unblock input when simulation is reset
        self.view.sidebar_component.set_input_blocked(False)
        
        # Switch back to Input tab after reset
        self.view.sidebar_component.main_tabs.setCurrentIndex(0)

    def skip_day(self):
        """
        Skip the day by simulating in the background.
        If the simulation hasn't started yet, initialize it first.
        """
        if not self.sim_manager.is_initialized:
            # Check if at least one checkout is open
            has_open_checkout = any(
                c.get("open", True)
                for c in self.map_manager.checkouts_data
            )
            if not has_open_checkout:
                title = (
                    self.translator.get(
                        "errors.no_open_checkout_title", "Fehler"
                    )
                    if self.translator
                    else "Fehler"
                )
                message = (
                    self.translator.get(
                        "errors.no_open_checkout_message",
                        "Mindestens eine Kasse (Normal oder SB) muss geöffnet sein, um den Tag zu überspringen.",
                    )
                    if self.translator
                    else "Mindestens eine Kasse (Normal oder SB) muss geöffnet sein, um den Tag zu überspringen."
                )
                QMessageBox.warning(self.view, title, message)
                return
            
            try:
                # Initialize the simulation first
                count = self.view.actor_count_input.value()
                prob = self.view.disabled_prob_input.value()
                ot = self.view.time_open.time()
                ct = self.view.time_close.time()
                self.sim_manager.init_day(count, prob, ot, ct)
                
                # Preload all input tabs before blocking
                self.view.sidebar_component.preload_all_input_tabs()
                # Block input when simulation starts
                self.view.sidebar_component.set_input_blocked(
                    True, self.translator
                )
                # Switch to statistics tab
                self.view.sidebar_component.main_tabs.setCurrentIndex(1)
            except Exception as e:
                QMessageBox.warning(
                    self.view, "Fehler", f"Ungültige Parameter: {e}"
                )
                return
        
        # Now skip the day (simulate in background)
        self.sim_manager.skip_day()
        self.view.btn_play_pause.setChecked(False)
        self._set_play_pause_icon(False)

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
            pay_ratio = (
                self.view.payment_cash.value(),
                self.view.payment_card.value(),
            )
            pay_cash_speed = (
                self.view.pay_duration_cash_min.value(),
                self.view.pay_duration_cash_max.value(),
            )
            pay_card_speed = (
                self.view.pay_duration_card_min.value(),
                self.view.pay_duration_card_max.value(),
            )
            pay_sb_speed = None
            if hasattr(self.view, "pay_duration_sb_min"):
                pay_sb_speed = (
                    self.view.pay_duration_sb_min.value(),
                    self.view.pay_duration_sb_max.value(),
                )
            fail_rate_normal = 0.0
            if hasattr(self.view, "checkout_fail_rate_normal"):
                fail_rate_normal = self.view.checkout_fail_rate_normal.value()
            fail_rate_sb = 0.0
            if hasattr(self.view, "checkout_fail_rate_sb"):
                fail_rate_sb = self.view.checkout_fail_rate_sb.value()
            customer_annoyance_rate = 0.0
            if hasattr(self.view, "customer_annoyance_rate"):
                customer_annoyance_rate = (
                    self.view.customer_annoyance_rate.value()
                )
            print(
                f"DEBUG: Getting UI params - customer_annoyance_rate: {customer_annoyance_rate}"
            )
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
                "pay_ratio": pay_ratio,
                "pay_cash_speed": pay_cash_speed,
                "pay_card_speed": pay_card_speed,
                "pay_sb_speed": pay_sb_speed,
                "checkout_fail_rate_normal": fail_rate_normal,
                "checkout_fail_rate_sb": fail_rate_sb,
                "customer_annoyance_rate": customer_annoyance_rate,
                "worker_repair_min": self.view.worker_repair_min.value(),
                "worker_repair_max": self.view.worker_repair_max.value(),
                "worker_conflict_min": self.view.worker_repair_min.value(),
                "worker_conflict_max": self.view.worker_repair_max.value(),
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
        spec = item.data(Qt.ItemDataRole.UserRole)
        if not spec:
            return
        self.visual_controller.draw_map_elements(self.map_manager)
        self.visual_controller.highlight_route(self.map_manager, spec)

    def on_object_selected(self, item):
        spec = item.data(Qt.ItemDataRole.UserRole)
        if spec:
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=spec
            )

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
        suffix_points = (
            self.translator.get("sidebar.editor.route_points_suffix")
            if self.translator
            else "Pkt"
        )
        label_start = (
            self.translator.get("sidebar.editor.route_label_start")
            if self.translator
            else "Start"
        )
        label_exit = (
            self.translator.get("sidebar.editor.route_label_exit")
            if self.translator
            else "Exit"
        )
        for name, pts in self.map_manager.shop_routes.items():
            item = QListWidgetItem(
                f"{name} ({len(pts)} {suffix_points})"
            )
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "shop_route", "name": name},
            )
            self.view.route_list_widget.addItem(item)
        for name, pts in self.map_manager.start_routes.items():
            item = QListWidgetItem(f"{name} ({label_start})")
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "start_route", "name": name},
            )
            self.view.route_list_widget.addItem(item)
        for name, pts in self.map_manager.exit_routes.items():
            item = QListWidgetItem(f"{name} ({label_exit})")
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "exit_route", "name": name},
            )
            self.view.route_list_widget.addItem(item)

    def _refresh_object_list(self):
        self.view.object_list_widget.clear()
        shelf_label = (
            self.translator.get("sidebar.editor.object_shelf")
            if self.translator
            else "Regal"
        )
        checkout_label = (
            self.translator.get("sidebar.editor.object_checkout")
            if self.translator
            else "Kasse"
        )
        for i, s in enumerate(self.map_manager.all_shelves):
            item = QListWidgetItem(
                f"{shelf_label} #{i} ({s.get('variant',0)})"
            )
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "shelf", "index": i}
            )
            self.view.object_list_widget.addItem(item)
        for c in self.map_manager.checkouts_data:
            item = QListWidgetItem(
                f"{checkout_label} #{c['id']} ({c['type']})"
            )
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "checkout", "id": c["id"]}
            )
            self.view.object_list_widget.addItem(item)

    def _highlight_list_item(self, list_widget, ID_val):
        for i in range(list_widget.count()):
            it = list_widget.item(i)
            if f"#{ID_val}" in it.text():
                it.setSelected(True)

    def on_back_to_menu(self):
        """Handle returning to main menu from simulation."""
        # Pause simulation if running
        if self.sim_manager.is_running:
            self.sim_manager.pause()
            self.view.btn_play_pause.setChecked(False)
            self._set_play_pause_icon(False)

        # Emit signal to application launcher to switch to menu screen
        self.view.back_to_menu_requested.emit()

    def _set_play_pause_icon(self, is_running: bool):
        icon = (
            self.view.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
            if is_running
            else self.view.style().standardIcon(
                QStyle.StandardPixmap.SP_MediaPlay
            )
        )
        self.view.btn_play_pause.setIcon(icon)
