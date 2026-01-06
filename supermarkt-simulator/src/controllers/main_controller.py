"""
Main Controller.
COMPLETE VERSION.
Includes:
- Simulation Loop & Spawning
- All Editor Tools (Start/Exit Routes, Areas, Shelves, Checkouts)
- Map Management (Load/Save/New/Delete/Background)
- Dialog Handlers (Visibility, Offsets, Sizes)
- Event Handling
"""

import json
import random
import os
import shutil
import math
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF, QTime
from PyQt6.QtGui import QPen, QBrush, QVector2D, QPainterPath, QColor, QPixmap
from PyQt6.QtWidgets import (
    QListWidgetItem,
    QGraphicsPathItem,
    QMessageBox,
    QInputDialog,
    QGraphicsItem,
    QGraphicsView,
    QFileDialog,
    QGraphicsPixmapItem
)
from config import *
from views.main_window import MainWindow
from views.size_config_dialog import SizeConfigDialog
from models.customer import CustomerModel

# Ensure all items are imported
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
    StartAreaItem,
    ExitAreaItem
)
from views.dialogs import (
    VisibilityDialog,
    OffsetDialog,
    ObjectPositionDialog,
    CheckoutConfigDialog,
)


class MainController:
    def __init__(self):
        # Data Containers
        self.shop_routes = {}
        self.start_routes = {}
        self.exit_routes = {}
        
        self.all_shelves = []
        self.checkouts_data = []
        
        self.waiting_area_rect = None
        self.start_area_rect = None
        self.exit_area_rect = None
        
        # Temp Drawing
        self.current_route_points = []
        self.current_route_path_item = None
        self.current_route_point_items = []
        
        # Background Logic
        self.background_image_path = None
        self.background_item = None
        self.background_scale = 1.0
        
        self.settings = DEFAULT_SETTINGS.copy()

        self.current_mode = "Simulation"
        self.active_tool = None
        self.active_tool_params = {}
        self.selected_object_spec = None

        self.sim_time = QTime(*DEFAULT_OPEN_TIME)
        self.open_time = QTime(*DEFAULT_OPEN_TIME)
        self.close_time = QTime(*DEFAULT_CLOSE_TIME)
        self.is_running = False
        self.time_factor = FACTOR_1X
        self.time_accumulator_sec = 0.0

        self.current_map_file = None
        if not MAPS_DIR.exists():
            os.makedirs(MAPS_DIR)
            
        # FIX: Use SETTINGS_FILE from config.py directly
        self.settings_file = SETTINGS_FILE

        # Simulation Objects
        self.customers_model = []
        self.customer_items = []
        self.checkout_queues = {}
        self.queue_count = 0
        
        # Visual Items Lists
        self.shelf_items = []
        self.checkout_items = []
        self.route_debug_items = []
        self.cashier_items = []
        self.waiting_area_item = None
        self.start_area_item = None
        self.exit_area_item = None

        # Spawning Logic
        self.target_daily_customers = 50
        self.spawn_timer_acc = 0.0
        self.next_spawn_interval = 0.0
        self.average_spawn_interval = 10.0
        self.prob_disabled = 0.1

        # Timer
        self.sim_timer = QTimer()
        self.sim_timer.setInterval(ANIMATION_TICK_MS)
        self.sim_timer.timeout.connect(self.simulation_tick)

        # View Init
        self.view = MainWindow()
        self.view.set_controller(self)
        self.scene = self.view.sim_scene

        # --- CONNECTIONS ---
        
        # Simulation Control
        self.view.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.view.btn_reset.clicked.connect(self.reset_simulation)
        self.view.btn_skip.clicked.connect(self.skip_day)
        self.view.btn_speed_1.clicked.connect(lambda: self.set_speed(FACTOR_1X))
        self.view.btn_speed_2.clicked.connect(lambda: self.set_speed(FACTOR_2X))
        self.view.btn_speed_3.clicked.connect(lambda: self.set_speed(FACTOR_6X))
        
        # Camera / View
        self.view.btn_reset_zoom.clicked.connect(self.view.reset_sim_zoom)
        self.view.map_combo.currentTextChanged.connect(self.on_map_selection_changed)
        self.view.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        # Map Management
        self.view.btn_new_map.clicked.connect(self.create_new_map)
        self.view.btn_save_map.clicked.connect(self.save_current_map)
        self.view.btn_delete_map.clicked.connect(self.delete_current_map)
        self.view.btn_set_background.clicked.connect(self.select_map_background)
        self.view.btn_remove_background.clicked.connect(self.remove_map_background)
        self.view.spin_bg_scale.valueChanged.connect(self.on_bg_scale_changed)

        # Tools
        self.view.new_route_button.clicked.connect(self.toggle_route_tool)
        self.view.place_shelves_button.clicked.connect(self.toggle_shelf_tool)
        self.view.waiting_area_button.clicked.connect(self.toggle_waiting_area_tool)
        self.view.start_area_button.clicked.connect(self.toggle_start_area_tool)
        self.view.btn_start_route.clicked.connect(self.toggle_start_route_tool)
        self.view.btn_exit_route.clicked.connect(self.toggle_exit_route_tool)
        self.view.btn_exit_area.clicked.connect(self.toggle_exit_area_tool)

        # Checkouts
        self.view.btn_kl.clicked.connect(lambda: self.toggle_checkout_tool("Normal", "Left", self.view.btn_kl))
        self.view.btn_kr.clicked.connect(lambda: self.toggle_checkout_tool("Normal", "Right", self.view.btn_kr))
        self.view.btn_sl.clicked.connect(lambda: self.toggle_checkout_tool("SB", "Left", self.view.btn_sl))
        self.view.btn_sr.clicked.connect(lambda: self.toggle_checkout_tool("SB", "Right", self.view.btn_sr))

        # Config Dialogs
        self.view.btn_visibility.clicked.connect(self.open_visibility_dialog)
        self.view.btn_offsets.clicked.connect(self.open_offsets_dialog)
        self.view.btn_config_sizes.clicked.connect(self.open_size_config_dialog)
        
        # Drawing Actions
        self.view.btn_save_admin.clicked.connect(self.finish_route_drawing)
        self.view.btn_cancel_route.clicked.connect(self.cancel_route_drawing)

        # Lists & Selection
        self.view.route_list_widget.itemClicked.connect(lambda i: None)
        self.view.object_list_widget.itemClicked.connect(self.on_object_list_clicked)
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.btn_edit_obj.clicked.connect(self.edit_selected_object)
        self.view.btn_del_obj.clicked.connect(self.delete_selected_object_from_list)

        # Scene Events
        self.scene.clicked_point.connect(self.handle_scene_click)
        self.scene.waiting_area_created.connect(self.handle_waiting_area_created)
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

        # Initialization
        self.load_settings()
        self.refresh_map_list()
        self.on_mode_changed("Simulation")
        self.update_clock_display()

        if self.view.sim_view:
            self.view.sim_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def show(self):
        self.view.show()

    def load_settings(self):
        if self.settings_file.exists():
            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))
        for k, v in DEFAULT_SETTINGS.items():
            if k not in self.settings:
                self.settings[k] = v

    # --- SIMULATION CONTROL ---

    def toggle_play_pause(self):
        if self.sim_timer.isActive():
            self.pause_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.shop_routes:
            QMessageBox.warning(self.view, "Warnung", "Keine Shop-Routen definiert!")
            self.view.btn_play_pause.setChecked(False)
            return
        if self.current_mode == "Editor":
            QMessageBox.warning(self.view, "Modus", "Bitte wechseln Sie in den Simulations-Modus.")
            self.view.btn_play_pause.setChecked(False)
            return
        if not self.is_running:
            self.initialize_simulation_day()
        self.is_running = True
        self.view.btn_play_pause.setChecked(True)
        self.view.btn_play_pause.setText("⏸")
        self.disable_inputs(True)
        self.sim_timer.start()

    def disable_inputs(self, disabled):
        self.view.time_open.setEnabled(not disabled)
        self.view.time_close.setEnabled(not disabled)
        self.view.actor_count_input.setEnabled(not disabled)
        self.view.disabled_prob_input.setEnabled(not disabled)

    def pause_simulation(self):
        self.sim_timer.stop()
        self.view.btn_play_pause.setChecked(False)
        self.view.btn_play_pause.setText("▶")
        self.is_running = False

    def reset_simulation(self):
        self.pause_simulation()
        self.clear_customers()
        self.sim_time = self.view.time_open.time()
        self.time_accumulator_sec = 0.0
        self.update_clock_display()
        self.disable_inputs(False)
        self.view.lbl_queue_count.setText("0")
        self.view.lbl_customers_in_store.setText("0")
        self.view.list_log.clear()
        self.is_running = False

    def clear_customers(self):
        for c in self.customer_items:
            self.scene.removeItem(c)
        self.customers_model.clear()
        self.customer_items.clear()
        self.checkout_queues = {}
        self.queue_count = 0

    def initialize_simulation_day(self):
        self.open_time = self.view.time_open.time()
        self.close_time = self.view.time_close.time()
        self.sim_time = self.open_time
        self.time_accumulator_sec = 0.0
        self.update_clock_display()
        self.clear_customers()
        self.draw_debug_elements()

        self.target_daily_customers = self.view.actor_count_input.value()
        self.prob_disabled = self.view.disabled_prob_input.value() / 100.0

        seconds_open = self.open_time.secsTo(self.close_time)
        if seconds_open <= 0: seconds_open = 1
        self.average_spawn_interval = seconds_open / max(1, self.target_daily_customers)
        self.spawn_timer_acc = 0.0
        self.calc_next_spawn()
        self.view.add_log_entry(f"Laden geöffnet. Erwarte ca. {self.target_daily_customers} Kunden.", "blue")

    def calc_next_spawn(self):
        variance = random.uniform(0.7, 1.3)
        self.next_spawn_interval = self.average_spawn_interval * variance

    def attempt_spawn(self, dt_game_seconds):
        self.spawn_timer_acc += dt_game_seconds
        if self.spawn_timer_acc >= self.next_spawn_interval:
            self.spawn_timer_acc = 0
            self.spawn_single_customer()
            self.calc_next_spawn()

    def spawn_single_customer(self):
        route_names = list(self.shop_routes.keys())
        if not route_names: return

        offset = self.settings.get("customer_path_offset", 10)
        r_name = random.choice(route_names)
        is_disabled = random.random() < self.prob_disabled

        # READ PARAMS FROM VIEW (Normal Distribution)
        walk_mean = self.view.speed_walk_mean.value()
        walk_std = self.view.speed_walk_std.value()
        
        roll_mean = self.view.speed_roll_mean.value()
        roll_std = self.view.speed_roll_std.value()
        
        items_mean = self.view.items_mean.value()
        items_std = self.view.items_std.value()
        
        # Scan Speed Ranges (Uniform)
        if is_disabled:
            scan_min = self.view.scan_speed_disabled_min.value()
            scan_max = self.view.scan_speed_disabled_max.value()
        else:
            scan_min = self.view.scan_speed_normal_min.value()
            scan_max = self.view.scan_speed_normal_max.value()

        model = CustomerModel(
            self.shop_routes[r_name],
            self.all_shelves,
            self.start_area_rect,
            self.waiting_area_rect,
            exit_area_rect=self.exit_area_rect,
            start_routes=self.start_routes,
            exit_routes=self.exit_routes,
            max_offset=offset,
            is_disabled=is_disabled,
            
            # Pass Parameters
            speed_walk_params=(walk_mean, walk_std),
            speed_roll_params=(roll_mean, roll_std),
            items_params=(items_mean, items_std),
            scan_speed_range=(scan_min, scan_max)
        )
        total_seconds_today = self.open_time.secsTo(self.sim_time)
        model.entry_time_sec = total_seconds_today

        self.customers_model.append(model)
        item = CustomerItem(model, size=self.settings.get("size_customer", 32))
        self.scene.addItem(item)
        self.customer_items.append(item)
        
        type_str = "Kunde (mit Einschränkung)" if is_disabled else "Kunde"
        self.view.add_log_entry(f"{type_str} hat den Laden betreten.", "green")

    def skip_day(self):
        self.pause_simulation()
        self.sim_time = self.close_time
        self.update_clock_display()
        self.view.add_log_entry("Tag übersprungen.", "orange")
        QMessageBox.information(self.view, "Simulation", "Tag wurde übersprungen / beendet.")
        self.reset_simulation()

    def set_speed(self, factor):
        self.time_factor = factor

    def simulation_tick(self):
        real_dt = ANIMATION_TICK_MS / 1000.0
        game_dt = real_dt * self.time_factor
        self.time_accumulator_sec += game_dt
        while self.time_accumulator_sec >= 60.0:
            self.sim_time = self.sim_time.addSecs(60)
            self.time_accumulator_sec -= 60.0
            self.update_clock_display()
        if self.sim_time >= self.close_time:
            self.pause_simulation()
            self.update_clock_display()
            self.view.add_log_entry("Feierabend! Laden geschlossen.", "red")
            QMessageBox.information(self.view, "Feierabend", "Der Supermarkt schließt jetzt.")
            return

        self.attempt_spawn(game_dt)

        active_models = []
        active_items = []
        waiting_cnt = 0
        customers_in_store = len(self.customers_model)
        
        for i, model in enumerate(self.customers_model):
            item = self.customer_items[i]
            model.tick(game_dt)
            item.sync_visuals()
            if model.state == "WAITING_AREA":
                waiting_cnt += 1
                if model.assigned_checkout_id is None:
                    self.try_assign_checkout(model)
            if model.state == "IN_QUEUE" and model.assigned_checkout_id is not None:
                q = self.checkout_queues.get(model.assigned_checkout_id, [])
                if q and q[0] == model:
                    if (QVector2D(model.pos) - QVector2D(model.target_pos)).length() < 5.0:
                        model.state = "SCANNING"
            if model.state == "LEAVING" and model.assigned_checkout_id is not None:
                cid = model.assigned_checkout_id
                if cid in self.checkout_queues and self.checkout_queues[cid] and self.checkout_queues[cid][0] == model:
                    self.checkout_queues[cid].pop(0)
                    self.advance_queue(cid)
                    model.assigned_checkout_id = None
            if model.state == "GONE":
                now_sec = self.open_time.secsTo(self.sim_time)
                duration = int((now_sec - model.entry_time_sec) / 60)
                self.view.add_log_entry(f"Kunde hat Laden nach {duration} Min verlassen.", "gray")
                self.scene.removeItem(item)
            else:
                active_models.append(model)
                active_items.append(item)
        self.customers_model = active_models
        self.customer_items = active_items
        self.view.lbl_queue_count.setText(str(waiting_cnt))
        self.view.lbl_customers_in_store.setText(str(customers_in_store))

    def update_clock_display(self):
        self.view.lbl_clock.setText(self.sim_time.toString("HH:mm"))

    # --- QUEUE & LOGIC ---

    def try_assign_checkout(self, model):
        candidates = []
        for c_data in self.checkouts_data:
            if not c_data.get("open", True): continue
            cid = c_data["id"]
            if len(self.checkout_queues.get(cid, [])) < c_data.get("max_queue", 5):
                candidates.append(cid)
        if candidates:
            chosen_id = random.choice(candidates)
            if chosen_id not in self.checkout_queues:
                self.checkout_queues[chosen_id] = []
            self.checkout_queues[chosen_id].append(model)
            self.set_queue_target(model, chosen_id, len(self.checkout_queues[chosen_id]) - 1)

    def advance_queue(self, cid):
        if cid not in self.checkout_queues: return
        for idx, model in enumerate(self.checkout_queues[cid]):
            self.set_queue_target(model, cid, idx)
            if model.state != "SCANNING": model.state = "IN_QUEUE"

    def set_queue_target(self, model, cid, q_index):
        c_data = next((x for x in self.checkouts_data if x["id"] == cid), None)
        if not c_data: return
        start_point, direction_vec = self._get_checkout_queue_geometry(c_data)
        offset_vec = direction_vec * (q_index * QUEUE_SPACING)
        target = start_point + offset_vec.toPointF()
        exit_dir = self.view.combo_global_exit.currentText()
        model.go_to_queue(target, cid, exit_dir)

    def _get_checkout_queue_geometry(self, c_data):
        cx, cy = c_data["x"], c_data["y"]
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
        ori = c_data.get("orientation", "Right")
        c_type = c_data["type"]
        angle = c_data.get("angle", 0)
        
        offset_key = "offset_queue_" + ("sb_" if c_type == "SB" else "") + ("left" if ori == "Left" else "right")
        off = self.settings.get(offset_key, [0, 0])
        qx_local, qy_local = off[0], off[1]
        
        center_x = cx + cw / 2
        center_y = cy + ch / 2
        p_global_unrot_x = cx + qx_local
        p_global_unrot_y = cy + qy_local
        
        start_point = self._get_rotated_point(p_global_unrot_x, p_global_unrot_y, center_x, center_y, angle)
        rad = math.radians(angle)
        dir_x = -math.sin(rad)
        dir_y = math.cos(rad)
        return start_point, QVector2D(dir_x, dir_y)

    def _get_rotated_point(self, x, y, cx, cy, angle_deg):
        rad = math.radians(angle_deg)
        tx = x - cx
        ty = y - cy
        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)
        return QPointF(rx + cx, ry + cy)

    # --- EVENT HANDLERS ---

    def on_mode_changed(self, mode_text):
        self.current_mode = mode_text
        self.view.update_sidebar_mode(mode_text)
        self.view.is_admin_mode = mode_text == "Editor"
        if mode_text == "Editor":
            if self.sim_timer.isActive():
                self.pause_simulation()
        else:
            self.reset_tools()
        self.draw_debug_elements()

    def on_checkout_clicked(self, checkout_id):
        if self.current_mode == "Simulation":
            c_data = next(
                (x for x in self.checkouts_data if x["id"] == checkout_id),
                None,
            )
            if not c_data:
                return
            dlg = CheckoutConfigDialog(c_data, self.view)
            if dlg.exec():
                c_data.update(dlg.get_data())
                self.draw_debug_elements()

    def on_object_list_clicked(self, item):
        d = item.data(Qt.ItemDataRole.UserRole)
        self.selected_object_spec = d
        self.draw_debug_elements()
        self.scene.blockSignals(True)
        self.scene.clearSelection()
        t_i = None
        if d["type"] == "checkout":
            for c in self.checkout_items:
                if c.data_id == d["id"]:
                    t_i = c
                    break
        elif d["type"] == "shelf":
            if d["index"] < len(self.shelf_items):
                t_i = self.shelf_items[d["index"]]
        if t_i: t_i.setSelected(True)
        self.scene.blockSignals(False)

    def on_scene_selection_changed(self):
        if self.current_mode != "Editor": return
        sel = self.scene.selectedItems()
        if not sel:
            if not self.scene.signalsBlocked():
                self.view.object_list_widget.clearSelection()
                self.selected_object_spec = None
            return
        item = sel[0]
        target_row = -1
        spec = None
        if isinstance(item, CheckoutItem):
            for row in range(self.view.object_list_widget.count()):
                w_item = self.view.object_list_widget.item(row)
                data = w_item.data(Qt.ItemDataRole.UserRole)
                if data["type"] == "checkout" and data["id"] == item.data_id:
                    target_row = row
                    spec = data
                    break
        elif isinstance(item, ShelfItem):
            if hasattr(item, "index"):
                for row in range(self.view.object_list_widget.count()):
                    w_item = self.view.object_list_widget.item(row)
                    data = w_item.data(Qt.ItemDataRole.UserRole)
                    if data["type"] == "shelf" and data["index"] == item.index:
                        target_row = row
                        spec = data
                        break
        if target_row != -1:
            self.view.object_list_widget.blockSignals(True)
            self.view.object_list_widget.setCurrentRow(target_row)
            self.view.object_list_widget.blockSignals(False)
            self.selected_object_spec = spec

    def draw_debug_elements(self):
        self.scene.blockSignals(True)
        
        # Keep background + quad
        for i in self.scene.items():
            if (i != self.background_item and i != self.view.item_q1 and i != self.view.item_q2 and i != self.view.item_q3 and i != self.view.item_q4):
                pass
        
        if self.waiting_area_item and self.waiting_area_item.scene(): self.scene.removeItem(self.waiting_area_item)
        if self.start_area_item and self.start_area_item.scene(): self.scene.removeItem(self.start_area_item)
        if self.exit_area_item and self.exit_area_item.scene(): self.scene.removeItem(self.exit_area_item)
            
        for i in self.shelf_items:
            if i.scene(): self.scene.removeItem(i)
        self.shelf_items.clear()
        for i in (self.checkout_items + self.cashier_items + self.route_debug_items):
            if i.scene(): self.scene.removeItem(i)
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()
        
        if self.background_item:
            self.background_item.setZValue(-100)
            self.background_item.setScale(self.background_scale)
            if not self.background_item.scene(): self.scene.addItem(self.background_item)

        def is_selected(obj_type, idx_or_id):
            if not self.selected_object_spec: return False
            if self.selected_object_spec["type"] != obj_type: return False
            if obj_type == "shelf": return self.selected_object_spec["index"] == idx_or_id
            if obj_type == "checkout": return self.selected_object_spec["id"] == idx_or_id
            return False

        if self.waiting_area_rect and self.settings.get("show_waiting_area", True):
            self.waiting_area_item = WaitingAreaItem(self.waiting_area_rect)
            self.scene.addItem(self.waiting_area_item)
        if self.start_area_rect and self.settings.get("show_start_area", True):
            self.start_area_item = StartAreaItem(self.start_area_rect)
            self.scene.addItem(self.start_area_item)
        if self.exit_area_rect:
            self.exit_area_item = ExitAreaItem(self.exit_area_rect)
            self.scene.addItem(self.exit_area_item)

        for idx, p in enumerate(self.all_shelves):
            show = self.settings["show_shelves"] or self.view.is_placing_shelves or is_selected("shelf", idx)
            if show:
                s = ShelfItem(p.x(), p.y(), index=idx, size=self.settings.get("size_shelf", 32))
                self.scene.addItem(s)
                self.shelf_items.append(s)

        for cd in self.checkouts_data:
            show = self.settings["show_checkouts"] or is_selected("checkout", cd["id"])
            if show:
                ori = cd.get("orientation", "Right")
                angle = cd.get("angle", 0)
                c_type = cd["type"]
                lo = self.settings["offset_light_sb_" + ("left" if ori == "Left" else "right")] if c_type == "SB" else self.settings["offset_light_normal_" + ("left" if ori == "Left" else "right")]
                ci = CheckoutItem(cd["x"], cd["y"], c_type, ori, cd["open"], self.settings["show_cashiers"], cd.get("id"), lo, width=self.settings.get("size_checkout_width", 100), height=self.settings.get("size_checkout_height", 100), angle=angle)
                ci.clicked.connect(self.on_checkout_clicked)
                self.scene.addItem(ci)
                self.checkout_items.append(ci)
                
                if self.settings["show_routes"] or self.view.highlight_queues:
                    start_pt, dir_vec = self._get_checkout_queue_geometry(cd)
                    end_pt = start_pt + (dir_vec * 60).toPointF()
                    pp = QPainterPath()
                    pp.moveTo(start_pt)
                    pp.lineTo(end_pt)
                    li = QGraphicsPathItem(pp)
                    li.setPen(QPen(COLOR_QUEUE_HIGHLIGHT, 3) if self.view.highlight_queues else QPen(QColor(200, 0, 0, 100), 2, Qt.PenStyle.DashLine))
                    self.scene.addItem(li)
                    self.route_debug_items.append(li)
                    
                if c_type == "Normal" and self.settings["show_cashiers"] and cd.get("open", True):
                    off_c = self.settings["offset_cashier_left"] if ori == "Left" else self.settings["offset_cashier_right"]
                    cw = self.settings.get("size_checkout_width", 100)
                    ch = self.settings.get("size_checkout_height", 100)
                    cx_center = cd["x"] + cw / 2
                    cy_center = cd["y"] + ch / 2
                    final_pos = self._get_rotated_point(cd["x"] + off_c[0], cd["y"] + off_c[1], cx_center, cy_center, angle)
                    cai = CashierItem(final_pos.x(), final_pos.y(), cd.get("skill", "Azubi"), size=self.settings.get("size_cashier", 22))
                    self.scene.addItem(cai)
                    self.cashier_items.append(cai)

        if self.settings["show_routes"]:
            pen = QPen(QColor(100, 100, 100, 100), 2, Qt.PenStyle.DotLine)
            for pts in self.shop_routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pi.setPen(pen)
                    pi.setZValue(4)
                    self.scene.addItem(pi)
                    self.route_debug_items.append(pi)
            
            for pts in self.start_routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pi.setPen(QPen(COLOR_BLUE, 2, Qt.PenStyle.DotLine))
                    pi.setZValue(4)
                    self.scene.addItem(pi)
                    self.route_debug_items.append(pi)

            for pts in self.exit_routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pi.setPen(QPen(COLOR_RED, 2, Qt.PenStyle.DotLine))
                    pi.setZValue(4)
                    self.scene.addItem(pi)
                    self.route_debug_items.append(pi)

        for i in self.shelf_items + self.checkout_items:
            i.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            i.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        if self.selected_object_spec:
            spec = self.selected_object_spec
            item_to_select = None
            if spec["type"] == "checkout":
                for c in self.checkout_items:
                    if c.data_id == spec["id"]:
                        item_to_select = c
                        break
            elif spec["type"] == "shelf":
                if spec["index"] < len(self.shelf_items):
                    item_to_select = self.shelf_items[spec["index"]]
            if item_to_select: item_to_select.setSelected(True)

        self.scene.blockSignals(False)
        self.update_object_list()

    # --- TOOLS & EDITOR ---

    def reset_tools(self, exclude_btn=None):
        tools = [
            self.view.new_route_button, self.view.place_shelves_button,
            self.view.waiting_area_button, self.view.start_area_button,
            self.view.btn_start_route, self.view.btn_exit_route, self.view.btn_exit_area,
            self.view.btn_kl, self.view.btn_kr, self.view.btn_sl, self.view.btn_sr,
        ]
        for btn in tools:
            if btn != exclude_btn: btn.setChecked(False)
        self.active_tool = None
        self.view.is_drawing_mode = False
        self.view.is_placing_shelves = False
        self.view.is_drawing_waiting_area = False
        self.view.is_placing_checkout = False
        self.view.is_drawing_start_area = False
        self.view.is_drawing_start_route = False
        self.view.is_drawing_exit_route = False
        self.view.is_drawing_exit_area = False
        self.view.admin_toolbar.hide()

        if self.current_route_path_item:
            if self.current_route_path_item.scene(): self.scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for i in self.current_route_point_items:
            if i.scene(): self.scene.removeItem(i)
        self.current_route_point_items.clear()

        if self.view.sim_view: self.view.sim_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def toggle_route_tool(self):
        self._toggle_generic_route("route", self.view.new_route_button, COLOR_ORANGE)

    def toggle_start_route_tool(self):
        self._toggle_generic_route("start_route", self.view.btn_start_route, COLOR_BLUE)

    def toggle_exit_route_tool(self):
        self._toggle_generic_route("exit_route", self.view.btn_exit_route, COLOR_RED)

    def _toggle_generic_route(self, tool_name, btn, color):
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = tool_name
            if tool_name == "route": self.view.is_drawing_mode = True
            elif tool_name == "start_route": self.view.is_drawing_start_route = True
            elif tool_name == "exit_route": self.view.is_drawing_exit_route = True
            self.view.admin_toolbar.show()
            self._init_temp_path(color)
        else:
            self.reset_tools()
            
    def cancel_route_drawing(self):
        """Cancels the current route drawing operation."""
        self.reset_tools()
        self.draw_debug_elements()

    def _init_temp_path(self, color):
        self.current_route_points = []
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(QPen(color, 3, Qt.PenStyle.DashLine))
        self.scene.addItem(self.current_route_path_item)
        if self.view.sim_view: self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)

    def toggle_shelf_tool(self):
        if self.view.place_shelves_button.isChecked():
            self.reset_tools(exclude_btn=self.view.place_shelves_button)
            self.active_tool = "shelf"
            self.view.is_placing_shelves = True
            self.draw_debug_elements()
            if self.view.sim_view: self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()
            self.draw_debug_elements()

    def toggle_waiting_area_tool(self):
        self._toggle_area_tool("waiting_area", self.view.waiting_area_button)

    def toggle_start_area_tool(self):
        self._toggle_area_tool("start_area", self.view.start_area_button)

    def toggle_exit_area_tool(self):
        self._toggle_area_tool("exit_area", self.view.btn_exit_area)

    def _toggle_area_tool(self, tool_name, btn):
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = tool_name
            if tool_name == "waiting_area": self.view.is_drawing_waiting_area = True
            elif tool_name == "start_area": self.view.is_drawing_start_area = True
            elif tool_name == "exit_area": self.view.is_drawing_exit_area = True
            if self.view.sim_view: self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def toggle_checkout_tool(self, c_type, ori, btn):
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "checkout"
            self.view.is_placing_checkout = True
            self.active_tool_params = {"type": c_type, "ori": ori}
            if self.view.sim_view: self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def handle_scene_click(self, pos):
        if self.current_mode != "Editor": return
        
        if self.active_tool in ["route", "start_route", "exit_route"]:
            self.current_route_points.append(pos)
            dot = self.scene.addEllipse(pos.x() - 4, pos.y() - 4, 8, 8, QPen(COLOR_DARK_TEXT), QBrush(COLOR_ORANGE))
            dot.setZValue(10)
            self.current_route_point_items.append(dot)
            if len(self.current_route_points) > 1:
                pp = QPainterPath()
                pp.moveTo(self.current_route_points[0])
                [pp.lineTo(x) for x in self.current_route_points[1:]]
                self.current_route_path_item.setPath(pp)
        elif self.active_tool == "shelf":
            self.all_shelves.append(pos)
            self.draw_debug_elements()
        elif self.active_tool == "checkout":
            new_id = (max(c["id"] for c in self.checkouts_data) + 1) if self.checkouts_data else 1
            self.checkouts_data.append({
                "id": new_id, "x": pos.x(), "y": pos.y(),
                "type": self.active_tool_params.get("type"),
                "orientation": self.active_tool_params.get("ori"),
                "open": True, "skill": "Azubi", "max_queue": 5, "angle": 0
            })
            self.draw_debug_elements()

    def finish_route_drawing(self):
        if self.current_route_points:
            if self.active_tool == "route":
                name = f"ShopRoute_{len(self.shop_routes)+1}"
                self.shop_routes[name] = list(self.current_route_points)
            elif self.active_tool == "start_route":
                name = f"StartRoute_{len(self.start_routes)+1}"
                self.start_routes[name] = list(self.current_route_points)
                QMessageBox.information(self.view, "Info", f"Start-Route '{name}' hinzugefügt.")
            elif self.active_tool == "exit_route":
                name = f"ExitRoute_{len(self.exit_routes)+1}"
                self.exit_routes[name] = list(self.current_route_points)
                QMessageBox.information(self.view, "Info", f"Ausgangs-Route '{name}' hinzugefügt.")
        self.reset_tools()
        self.draw_debug_elements()

    def handle_waiting_area_created(self, rect):
        if self.active_tool == "waiting_area": self.waiting_area_rect = rect
        elif self.active_tool == "start_area": self.start_area_rect = rect
        elif self.active_tool == "exit_area": self.exit_area_rect = rect
        self.draw_debug_elements()

    def delete_selected_route(self):
        item = self.view.route_list_widget.currentItem()
        if not item: return
        name = item.text()
        
        if name in self.shop_routes: del self.shop_routes[name]
        elif name in self.start_routes: del self.start_routes[name]
        elif name in self.exit_routes: del self.exit_routes[name]
            
        self.view.route_list_widget.takeItem(self.view.route_list_widget.row(item))
        self.draw_debug_elements()

    def update_object_list(self):
        self.view.route_list_widget.clear()
        for r in self.shop_routes: self.view.route_list_widget.addItem(r)
        for r in self.start_routes: self.view.route_list_widget.addItem(r)
        for r in self.exit_routes: self.view.route_list_widget.addItem(r)

        self.view.object_list_widget.clear()
        for c in self.checkouts_data:
            label = f"Kasse #{c.get('id')} ({c.get('type')})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {"type": "checkout", "id": c.get("id")})
            self.view.object_list_widget.addItem(item)
        for idx, p in enumerate(self.all_shelves):
            label = f"Regal #{idx+1} ({int(p.x())}, {int(p.y())})"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {"type": "shelf", "index": idx})
            self.view.object_list_widget.addItem(item)
        if self.selected_object_spec:
            spec = self.selected_object_spec
            for row in range(self.view.object_list_widget.count()):
                it = self.view.object_list_widget.item(row)
                d = it.data(Qt.ItemDataRole.UserRole)
                if d["type"] == spec["type"]:
                    if spec["type"] == "checkout" and d["id"] == spec["id"]:
                        self.view.object_list_widget.setCurrentRow(row)
                        break
                    elif spec["type"] == "shelf" and d["index"] == spec["index"]:
                        self.view.object_list_widget.setCurrentRow(row)
                        break

    # --- MAP FILES ---

    def create_new_map(self):
        name, ok = QInputDialog.getText(self.view, "Neue Map", "Name (ohne .json):")
        if ok and name:
            if not name.endswith(".json"): name += ".json"
            path = MAPS_DIR / name
            default_data = {"routes": {}, "start_routes": {}, "exit_routes": {}, "shelves": [], "checkouts": []}
            with open(path, "w") as f:
                json.dump(default_data, f, indent=4)
            self.refresh_map_list()
            self.view.map_combo.setCurrentText(name)

    def delete_current_map(self):
        if not self.current_map_file or self.current_map_file.name == "default.json":
            QMessageBox.warning(self.view, "Warnung", "Standard-Map kann nicht gelöscht werden.")
            return
        reply = QMessageBox.question(self.view, "Löschen", f"'{self.current_map_file.name}' löschen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.current_map_file)
                self.current_map_file = None
                self.refresh_map_list()
            except Exception as e:
                QMessageBox.critical(self.view, "Fehler", f"Löschen fehlgeschlagen: {e}")

    def refresh_map_list(self):
        self.view.map_combo.blockSignals(True)
        self.view.map_combo.clear()
        maps = sorted([f.name for f in MAPS_DIR.glob("*.json")])
        if not maps:
            self.create_default_map()
            maps = ["default.json"]
        self.view.map_combo.addItems(maps)
        target_map = maps[0]
        if self.current_map_file and self.current_map_file.name in maps:
            target_map = self.current_map_file.name
        self.view.map_combo.setCurrentText(target_map)
        self.view.map_combo.blockSignals(False)
        if self.current_map_file is None or self.current_map_file.name != target_map:
            self.load_map(target_map)

    def create_default_map(self):
        default_data = {"routes": {}, "shelves": [], "checkouts": []}
        with open(MAPS_DIR / "default.json", "w") as f:
            json.dump(default_data, f, indent=4)

    def on_map_selection_changed(self, map_name):
        if map_name: self.load_map(map_name)

    def load_map(self, map_name):
        file_path = MAPS_DIR / map_name
        if not file_path.exists(): return
        self.current_map_file = file_path
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            def load_routes(key):
                res = {}
                if key in data:
                    raw = data[key]
                    if isinstance(raw, dict):
                        for name, pts in raw.items():
                            res[name] = [QPointF(p[0], p[1]) for p in pts]
                    elif isinstance(raw, list):
                        res["Route_Legacy"] = [QPointF(p[0], p[1]) for p in raw]
                return res

            self.shop_routes = load_routes("routes")
            self.start_routes = load_routes("start_routes")
            self.exit_routes = load_routes("exit_routes")

            raw_shelves = data.get("shelves", [])
            self.all_shelves = []
            for s in raw_shelves:
                if isinstance(s, dict): self.all_shelves.append(QPointF(s["x"], s["y"]))
                elif isinstance(s, list): self.all_shelves.append(QPointF(s[0], s[1]))

            self.checkouts_data = data.get("checkouts", [])
            self.waiting_area_rect = QRectF(*data["waiting_area"]) if data.get("waiting_area") else None
            self.start_area_rect = QRectF(*data["start_area"]) if data.get("start_area") else None
            self.exit_area_rect = QRectF(*data["exit_area"]) if data.get("exit_area") else None

            global_exit = data.get("global_exit_direction", "Rechts")
            self.view.combo_global_exit.setCurrentText(global_exit)
            
            self.background_image_path = data.get("background_image", None)
            self.background_scale = data.get("background_scale", 1.0)
            self.view.spin_bg_scale.blockSignals(True)
            self.view.spin_bg_scale.setValue(self.background_scale)
            self.view.spin_bg_scale.blockSignals(False)
            
            if self.background_item and self.background_item.scene(): self.scene.removeItem(self.background_item)
            self.background_item = None
            if self.background_image_path:
                bg_path = MAPS_DIR / self.background_image_path
                if bg_path.exists():
                    pix = QPixmap(str(bg_path))
                    self.background_item = QGraphicsPixmapItem(pix)
                    self.background_item.setZValue(-100)
                    self.background_item.setScale(self.background_scale)
                    self.scene.addItem(self.background_item)

            self.update_object_list()
            self.draw_debug_elements()
            self.on_mode_changed(self.current_mode)
            print(f"Loaded Map: {map_name}")
        except Exception as e:
            print(f"Error loading map: {e}")

    def save_current_map(self):
        if not self.current_map_file: return
        
        def export_routes(routes_dict):
            return {name: [[p.x(), p.y()] for p in pts] for name, pts in routes_dict.items()}

        routes_export = export_routes(self.shop_routes)
        start_routes_export = export_routes(self.start_routes)
        exit_routes_export = export_routes(self.exit_routes)
        
        shelves_export = [[p.x(), p.y()] for p in self.all_shelves]
        wa_export = [self.waiting_area_rect.x(), self.waiting_area_rect.y(), self.waiting_area_rect.width(), self.waiting_area_rect.height()] if self.waiting_area_rect else None
        sa_export = [self.start_area_rect.x(), self.start_area_rect.y(), self.start_area_rect.width(), self.start_area_rect.height()] if self.start_area_rect else None
        ea_export = [self.exit_area_rect.x(), self.exit_area_rect.y(), self.exit_area_rect.width(), self.exit_area_rect.height()] if self.exit_area_rect else None

        data = {
            "routes": routes_export,
            "start_routes": start_routes_export,
            "exit_routes": exit_routes_export,
            "shelves": shelves_export,
            "checkouts": self.checkouts_data,
            "waiting_area": wa_export,
            "start_area": sa_export,
            "exit_area": ea_export,
            "global_exit_direction": self.view.combo_global_exit.currentText(),
            "background_image": self.background_image_path,
            "background_scale": self.background_scale
        }
        try:
            with open(self.current_map_file, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self.view, "Gespeichert", f"Map '{self.current_map_file.name}' gespeichert.")
        except Exception as e:
            QMessageBox.critical(self.view, "Fehler", f"Fehler: {e}")

    # --- BG ---
    def select_map_background(self):
        if not self.current_map_file: return
        file_path, _ = QFileDialog.getOpenFileName(self.view, "Hintergrundbild wählen", str(IMAGE_DIR), "Bilder (*.png *.jpg *.jpeg)")
        if file_path:
            src = Path(file_path)
            dest_name = f"bg_{self.current_map_file.stem}{src.suffix}"
            dest_path = MAPS_DIR / dest_name
            try:
                shutil.copy(src, dest_path)
                self.background_image_path = dest_name
                self.background_scale = 1.0
                self.save_current_map()
                self.load_map(self.current_map_file.name)
            except Exception as e:
                QMessageBox.critical(self.view, "Fehler", f"Bild konnte nicht kopiert werden: {e}")

    def remove_map_background(self):
        if self.background_image_path:
            reply = QMessageBox.question(self.view, "Hintergrund entfernen", "Wirklich entfernen?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.background_image_path = None
                self.background_scale = 1.0
                if self.background_item and self.background_item.scene(): self.scene.removeItem(self.background_item)
                self.background_item = None
                self.save_current_map()

    def on_bg_scale_changed(self, value):
        self.background_scale = value
        if self.background_item: self.background_item.setScale(value)

    # --- DIALOGS (Wurden vorher vergessen) ---

    def open_visibility_dialog(self):
        """Öffnet den Dialog für Sichtbarkeitseinstellungen."""
        dlg = VisibilityDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.draw_debug_elements()

    def open_offsets_dialog(self):
        """Öffnet den Dialog für Offsets (Warteschlangen, Kassierer)."""
        self.view.highlight_queues = True
        self.draw_debug_elements()
        dlg = OffsetDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.view.highlight_queues = False
        self.draw_debug_elements()
        
    def open_size_config_dialog(self):
        """Öffnet den Dialog für Größenkonfigurationen."""
        dlg = SizeConfigDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.draw_debug_elements()

    # --- EDIT OBJECT ---
    def edit_selected_object(self):
        item = self.view.object_list_widget.currentItem()
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        obj_type = data["type"]
        cx, cy, name, cur_ori, cur_ang = 0, 0, "Objekt", None, 0
        if obj_type == "shelf":
            if data["index"] < len(self.all_shelves):
                pt = self.all_shelves[data["index"]]
                cx, cy, name = pt.x(), pt.y(), f"Regal #{data['index']+1}"
        elif obj_type == "checkout":
            cid = data["id"]
            c_data = next((c for c in self.checkouts_data if c["id"] == cid), None)
            if c_data:
                cx, cy, name, cur_ori, cur_ang = c_data["x"], c_data["y"], f"Kasse #{cid}", c_data.get("orientation", "Right"), c_data.get("angle", 0)
        
        dlg = ObjectPositionDialog(name, cx, cy, orientation=cur_ori, angle=cur_ang, parent=self.view)
        
        def update_pos(nx, ny):
            if obj_type == "shelf": self.all_shelves[data["index"]] = QPointF(nx, ny)
            elif obj_type == "checkout": 
                c = next((x for x in self.checkouts_data if x["id"] == data["id"]), None)
                if c: c["x"], c["y"] = nx, ny
            self.draw_debug_elements()
        
        def update_ori(no):
            c = next((x for x in self.checkouts_data if x["id"] == data["id"]), None)
            if c: c["orientation"] = no
            self.draw_debug_elements()

        def update_ang(na):
            c = next((x for x in self.checkouts_data if x["id"] == data["id"]), None)
            if c: c["angle"] = na
            self.draw_debug_elements()

        dlg.position_changed.connect(update_pos)
        if cur_ori: 
            dlg.orientation_changed.connect(update_ori)
            dlg.angle_changed.connect(update_ang)
        
        dlg.exec()
        self.draw_debug_elements()

    def delete_selected_object_from_list(self):
        item = self.view.object_list_widget.currentItem()
        if not item: return
        d = item.data(Qt.ItemDataRole.UserRole)
        if d["type"] == "shelf":
            if d["index"] < len(self.all_shelves): del self.all_shelves[d["index"]]
        elif d["type"] == "checkout":
            self.checkouts_data = [c for c in self.checkouts_data if c["id"] != d["id"]]
        self.selected_object_spec = None
        self.draw_debug_elements()