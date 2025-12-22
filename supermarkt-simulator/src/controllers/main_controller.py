"""
Main Controller.
Refactored: Distributed spawning over the day, Live Feed integration.
"""

import json
import random
import os
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF, QTime
from PyQt6.QtGui import QPen, QBrush, QVector2D, QPainterPath, QColor
from PyQt6.QtWidgets import (
    QListWidgetItem,
    QGraphicsPathItem,
    QMessageBox,
    QInputDialog,
    QGraphicsItem,
    QGraphicsView,
)
from config import *
from views.main_window import MainWindow
from models.customer import CustomerModel

# Ensure all items are imported
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
    StartAreaItem,
)
from views.dialogs import (
    VisibilityDialog,
    OffsetDialog,
    ObjectPositionDialog,
    CheckoutConfigDialog,
)


class MainController:
    def __init__(self):
        self.all_routes = {}
        self.all_shelves = []
        self.checkouts_data = []
        self.waiting_area_rect = None
        self.start_area_rect = None
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
        self.settings_file = BASE_DIR / "settings.json"

        self.customers_model = []
        self.customer_items = []
        self.checkout_queues = {}
        self.queue_count = 0
        self.shelf_items = []
        self.checkout_items = []
        self.route_debug_items = []
        self.cashier_items = []
        self.waiting_area_item = None
        self.start_area_item = None

        # SPAWNING LOGIC
        self.target_daily_customers = 50
        self.spawn_timer_acc = 0.0
        self.next_spawn_interval = 0.0
        self.average_spawn_interval = 10.0
        self.prob_disabled = 0.1

        self.current_route_points = []
        self.current_route_path_item = None
        self.current_route_point_items = []

        self.sim_timer = QTimer()
        self.sim_timer.setInterval(ANIMATION_TICK_MS)
        self.sim_timer.timeout.connect(self.simulation_tick)

        self.view = MainWindow()
        self.view.set_controller(self)
        self.scene = self.view.sim_scene

        # Connections
        self.view.btn_play_pause.clicked.connect(self.toggle_play_pause)
        self.view.btn_reset.clicked.connect(self.reset_simulation)
        self.view.btn_skip.clicked.connect(self.skip_day)
        self.view.btn_speed_1.clicked.connect(
            lambda: self.set_speed(FACTOR_1X)
        )
        self.view.btn_speed_2.clicked.connect(
            lambda: self.set_speed(FACTOR_2X)
        )
        self.view.btn_speed_3.clicked.connect(
            lambda: self.set_speed(FACTOR_6X)
        )
        self.view.btn_reset_zoom.clicked.connect(self.view.reset_sim_zoom)
        self.view.map_combo.currentTextChanged.connect(
            self.on_map_selection_changed
        )
        self.view.mode_combo.currentTextChanged.connect(self.on_mode_changed)

        self.view.btn_new_map.clicked.connect(self.create_new_map)
        self.view.btn_save_map.clicked.connect(self.save_current_map)
        self.view.btn_delete_map.clicked.connect(self.delete_current_map)

        self.view.new_route_button.clicked.connect(self.toggle_route_tool)
        self.view.place_shelves_button.clicked.connect(self.toggle_shelf_tool)
        self.view.waiting_area_button.clicked.connect(
            self.toggle_waiting_area_tool
        )
        self.view.start_area_button.clicked.connect(
            self.toggle_start_area_tool
        )

        self.view.btn_kl.clicked.connect(
            lambda: self.toggle_checkout_tool(
                "Normal", "Left", self.view.btn_kl
            )
        )
        self.view.btn_kr.clicked.connect(
            lambda: self.toggle_checkout_tool(
                "Normal", "Right", self.view.btn_kr
            )
        )
        self.view.btn_sl.clicked.connect(
            lambda: self.toggle_checkout_tool("SB", "Left", self.view.btn_sl)
        )
        self.view.btn_sr.clicked.connect(
            lambda: self.toggle_checkout_tool("SB", "Right", self.view.btn_sr)
        )

        self.view.btn_visibility.clicked.connect(self.open_visibility_dialog)
        self.view.btn_offsets.clicked.connect(self.open_offsets_dialog)
        self.view.btn_save_admin.clicked.connect(self.finish_route_drawing)

        self.view.route_list_widget.itemClicked.connect(lambda i: None)
        self.view.object_list_widget.itemClicked.connect(
            self.on_object_list_clicked
        )
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.btn_edit_obj.clicked.connect(self.edit_selected_object)
        self.view.btn_del_obj.clicked.connect(
            self.delete_selected_object_from_list
        )

        self.scene.clicked_point.connect(self.handle_scene_click)
        self.scene.waiting_area_created.connect(
            self.handle_waiting_area_created
        )
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

        self.load_settings()
        self.refresh_map_list()
        self.on_mode_changed("Simulation")
        self.update_clock_display()

        # Set initial drag mode (Navigation)
        if self.view.sim_view:
            self.view.sim_view.setDragMode(
                QGraphicsView.DragMode.ScrollHandDrag
            )

    def show(self):
        self.view.show()

    def load_settings(self):
        if self.settings_file.exists():
            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))

    def toggle_play_pause(self):
        if self.sim_timer.isActive():
            self.pause_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.all_routes:
            QMessageBox.warning(
                self.view, "Warnung", "Keine Routen definiert!"
            )
            self.view.btn_play_pause.setChecked(False)
            return
        if self.current_mode == "Editor":
            QMessageBox.warning(
                self.view,
                "Modus",
                "Bitte wechseln Sie in den Simulations-Modus.",
            )
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

        # Init Spawning Parameters
        self.target_daily_customers = self.view.actor_count_input.value()
        self.prob_disabled = self.view.disabled_prob_input.value() / 100.0

        # Calculate Spawn Interval:
        # Total Minutes Open
        seconds_open = self.open_time.secsTo(self.close_time)
        if seconds_open <= 0:
            seconds_open = 1  # Avoid div by zero

        # e.g., 720 mins / 50 customers = 14.4 mins per customer (Game Time)
        self.average_spawn_interval = seconds_open / max(
            1, self.target_daily_customers
        )
        self.spawn_timer_acc = 0.0
        self.calc_next_spawn()

        self.view.add_log_entry(
            f"Laden geöffnet. Erwarte ca. {self.target_daily_customers} Kunden.",
            "blue",
        )

    def calc_next_spawn(self):
        # Random variance +/- 30% for organic feel
        variance = random.uniform(0.7, 1.3)
        self.next_spawn_interval = self.average_spawn_interval * variance

    def attempt_spawn(self, dt_game_seconds):
        self.spawn_timer_acc += dt_game_seconds
        if self.spawn_timer_acc >= self.next_spawn_interval:
            self.spawn_timer_acc = 0
            self.spawn_single_customer()
            self.calc_next_spawn()

    def spawn_single_customer(self):
        route_names = list(self.all_routes.keys())
        if not route_names:
            return

        offset = self.settings.get("customer_path_offset", 10)
        r_name = random.choice(route_names)

        # Determine Type
        is_disabled = random.random() < self.prob_disabled

        model = CustomerModel(
            self.all_routes[r_name],
            self.all_shelves,
            self.start_area_rect,
            self.waiting_area_rect,
            max_offset=offset,
            is_disabled=is_disabled,
        )

        # Set Entry Time for Log
        total_seconds_today = self.open_time.secsTo(self.sim_time)
        model.entry_time_sec = total_seconds_today

        self.customers_model.append(model)
        item = CustomerItem(model)
        self.scene.addItem(item)
        self.customer_items.append(item)

        type_str = "Kunde (mit Einschränkung)" if is_disabled else "Kunde"
        self.view.add_log_entry(f"{type_str} hat den Laden betreten.", "green")

    def skip_day(self):
        self.pause_simulation()
        self.sim_time = self.close_time
        self.update_clock_display()
        self.view.add_log_entry("Tag übersprungen.", "orange")
        QMessageBox.information(
            self.view, "Simulation", "Tag wurde übersprungen / beendet."
        )
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
            QMessageBox.information(
                self.view, "Feierabend", "Der Supermarkt schließt jetzt."
            )
            return

        # Spawning Logic
        self.attempt_spawn(game_dt)

        active_models = []
        active_items = []
        waiting_cnt = 0
        for i, model in enumerate(self.customers_model):
            item = self.customer_items[i]
            model.tick(game_dt)
            item.sync_visuals()
            if model.state == "WAITING_AREA":
                waiting_cnt += 1
                if model.assigned_checkout_id is None:
                    self.try_assign_checkout(model)
            if (
                model.state == "IN_QUEUE"
                and model.assigned_checkout_id is not None
            ):
                q = self.checkout_queues.get(model.assigned_checkout_id, [])
                if q and q[0] == model:
                    if (
                        QVector2D(model.pos) - QVector2D(model.target_pos)
                    ).length() < 5.0:
                        model.state = "SCANNING"
            if (
                model.state == "LEAVING"
                and model.assigned_checkout_id is not None
            ):
                cid = model.assigned_checkout_id
                if (
                    cid in self.checkout_queues
                    and self.checkout_queues[cid]
                    and self.checkout_queues[cid][0] == model
                ):
                    self.checkout_queues[cid].pop(0)
                    self.advance_queue(cid)
                    model.assigned_checkout_id = None
            if model.state == "GONE":
                # Log Leaving
                now_sec = self.open_time.secsTo(self.sim_time)
                duration = int(
                    (now_sec - model.entry_time_sec) / 60
                )  # in minutes
                self.view.add_log_entry(
                    f"Kunde hat Laden nach {duration} Min verlassen.", "gray"
                )
                self.scene.removeItem(item)
            else:
                active_models.append(model)
                active_items.append(item)
        self.customers_model = active_models
        self.customer_items = active_items
        self.view.lbl_queue_count.setText(str(waiting_cnt))

    def update_clock_display(self):
        self.view.lbl_clock.setText(self.sim_time.toString("HH:mm"))

    def try_assign_checkout(self, model):
        candidates = []
        for c_data in self.checkouts_data:
            if not c_data.get("open", True):
                continue
            cid = c_data["id"]
            if len(self.checkout_queues.get(cid, [])) < c_data.get(
                "max_queue", 5
            ):
                candidates.append(cid)
        if candidates:
            chosen_id = random.choice(candidates)
            if chosen_id not in self.checkout_queues:
                self.checkout_queues[chosen_id] = []
            self.checkout_queues[chosen_id].append(model)
            self.set_queue_target(
                model, chosen_id, len(self.checkout_queues[chosen_id]) - 1
            )

    def advance_queue(self, cid):
        if cid not in self.checkout_queues:
            return
        for idx, model in enumerate(self.checkout_queues[cid]):
            self.set_queue_target(model, cid, idx)
            if model.state != "SCANNING":
                model.state = "IN_QUEUE"

    def set_queue_target(self, model, cid, q_index):
        c_data = next((x for x in self.checkouts_data if x["id"] == cid), None)
        if not c_data:
            return
        cx, cy = c_data["x"], c_data["y"]
        ori = c_data.get("orientation", "Right")
        exit_dir = self.view.combo_global_exit.currentText()

        c_type = c_data["type"]
        offset_key = (
            "offset_queue_"
            + ("sb_" if c_type == "SB" else "")
            + ("left" if ori == "Left" else "right")
        )
        off = self.settings[offset_key]
        sx = cx + off[0]
        sy = cy + off[1]
        target = QPointF(sx, sy + (q_index * QUEUE_SPACING))
        model.go_to_queue(target, cid, exit_dir)

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
        if t_i:
            t_i.setSelected(True)
        self.scene.blockSignals(False)

    def on_scene_selection_changed(self):
        if self.current_mode != "Editor":
            return
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
        if self.waiting_area_item and self.waiting_area_item.scene():
            self.scene.removeItem(self.waiting_area_item)
        if self.start_area_item and self.start_area_item.scene():
            self.scene.removeItem(self.start_area_item)
        for i in self.shelf_items:
            if i.scene():
                self.scene.removeItem(i)
        self.shelf_items.clear()
        for i in (
            self.checkout_items + self.cashier_items + self.route_debug_items
        ):
            if i.scene():
                self.scene.removeItem(i)
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()

        def is_selected(obj_type, idx_or_id):
            if not self.selected_object_spec:
                return False
            if self.selected_object_spec["type"] != obj_type:
                return False
            if obj_type == "shelf":
                return self.selected_object_spec["index"] == idx_or_id
            if obj_type == "checkout":
                return self.selected_object_spec["id"] == idx_or_id
            return False

        if self.waiting_area_rect and self.settings.get(
            "show_waiting_area", True
        ):
            self.waiting_area_item = WaitingAreaItem(self.waiting_area_rect)
            self.scene.addItem(self.waiting_area_item)
        if self.start_area_rect and self.settings.get("show_start_area", True):
            self.start_area_item = StartAreaItem(self.start_area_rect)
            self.scene.addItem(self.start_area_item)

        for idx, p in enumerate(self.all_shelves):
            show = (
                self.settings["show_shelves"]
                or self.view.is_placing_shelves
                or is_selected("shelf", idx)
            )
            if show:
                # Assuming simple QPointF from previous revert
                s = ShelfItem(p.x(), p.y(), index=idx)
                self.scene.addItem(s)
                self.shelf_items.append(s)

        for cd in self.checkouts_data:
            show = self.settings["show_checkouts"] or is_selected(
                "checkout", cd["id"]
            )
            if show:
                ori = cd.get("orientation", "Right")
                c_type = cd["type"]
                lo = (
                    self.settings[
                        "offset_light_sb_"
                        + ("left" if ori == "Left" else "right")
                    ]
                    if c_type == "SB"
                    else self.settings[
                        "offset_light_normal_"
                        + ("left" if ori == "Left" else "right")
                    ]
                )
                ci = CheckoutItem(
                    cd["x"],
                    cd["y"],
                    c_type,
                    ori,
                    cd["open"],
                    self.settings["show_cashiers"],
                    cd.get("id"),
                    lo,
                )
                ci.clicked.connect(self.on_checkout_clicked)
                self.scene.addItem(ci)
                self.checkout_items.append(ci)
                if self.settings["show_routes"] or self.view.highlight_queues:
                    off = self.settings[
                        "offset_queue_"
                        + ("sb_" if c_type == "SB" else "")
                        + ("left" if ori == "Left" else "right")
                    ]
                    sx = cd["x"] + off[0]
                    sy = cd["y"] + off[1]
                    pp = QPainterPath()
                    pp.moveTo(sx, sy)
                    pp.lineTo(sx, sy + 60)
                    li = QGraphicsPathItem(pp)
                    li.setPen(
                        QPen(COLOR_QUEUE_HIGHLIGHT, 3)
                        if self.view.highlight_queues
                        else QPen(
                            QColor(200, 0, 0, 100), 2, Qt.PenStyle.DashLine
                        )
                    )
                    self.scene.addItem(li)
                    self.route_debug_items.append(li)
                if (
                    c_type == "Normal"
                    and self.settings["show_cashiers"]
                    and cd.get("open", True)
                ):
                    off_c = (
                        self.settings["offset_cashier_left"]
                        if ori == "Left"
                        else self.settings["offset_cashier_right"]
                    )
                    cai = CashierItem(
                        cd["x"] + off_c[0],
                        cd["y"] + off_c[1],
                        cd.get("skill", "Azubi"),
                    )
                    self.scene.addItem(cai)
                    self.cashier_items.append(cai)

        if self.settings["show_routes"]:
            pen = QPen(QColor(100, 100, 100, 100), 2, Qt.PenStyle.DotLine)
            for pts in self.all_routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pi.setPen(pen)
                    pi.setZValue(4)
                    self.scene.addItem(pi)
                    self.route_debug_items.append(pi)

        for i in self.shelf_items:
            i.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            i.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        for i in self.checkout_items:
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
            if item_to_select:
                item_to_select.setSelected(True)

        self.scene.blockSignals(False)
        self.update_object_list()

    # FIX: Reset tools now restores standard navigation mode (ScrollHandDrag)
    def reset_tools(self, exclude_btn=None):
        tools = [
            self.view.new_route_button,
            self.view.place_shelves_button,
            self.view.waiting_area_button,
            self.view.start_area_button,
            self.view.btn_kl,
            self.view.btn_kr,
            self.view.btn_sl,
            self.view.btn_sr,
        ]
        for btn in tools:
            if btn != exclude_btn:
                btn.setChecked(False)
        self.active_tool = None
        self.view.is_drawing_mode = False
        self.view.is_placing_shelves = False
        self.view.is_drawing_waiting_area = False
        self.view.is_placing_checkout = False
        self.view.is_drawing_start_area = False
        self.view.admin_toolbar.hide()

        if self.current_route_path_item:
            if self.current_route_path_item.scene():
                self.scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for i in self.current_route_point_items:
            if i.scene():
                self.scene.removeItem(i)
        self.current_route_point_items.clear()

        # RESTORE DRAG MODE FOR NAVIGATION
        if self.view.sim_view:
            self.view.sim_view.setDragMode(
                QGraphicsView.DragMode.ScrollHandDrag
            )

    def toggle_route_tool(self):
        btn = self.view.new_route_button
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "route"
            self.view.is_drawing_mode = True
            self.view.admin_toolbar.show()
            self.current_route_points = []
            self.current_route_path_item = QGraphicsPathItem()
            self.current_route_path_item.setPen(
                QPen(COLOR_ORANGE, 3, Qt.PenStyle.DashLine)
            )
            self.scene.addItem(self.current_route_path_item)
            # DISABLE DRAG FOR DRAWING
            if self.view.sim_view:
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def toggle_shelf_tool(self):
        btn = self.view.place_shelves_button
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "shelf"
            self.view.is_placing_shelves = True
            self.draw_debug_elements()
            # DISABLE DRAG
            if self.view.sim_view:
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()
            self.draw_debug_elements()

    def toggle_waiting_area_tool(self):
        btn = self.view.waiting_area_button
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "waiting_area"
            self.view.is_drawing_waiting_area = True
            if self.waiting_area_item:
                self.waiting_area_item.setVisible(True)
            # DISABLE DRAG
            if self.view.sim_view:
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def toggle_start_area_tool(self):
        btn = self.view.start_area_button
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "start_area"
            self.view.is_drawing_start_area = True
            if self.start_area_item:
                self.start_area_item.setVisible(True)
            # DISABLE DRAG
            if self.view.sim_view:
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def toggle_checkout_tool(self, c_type, ori, btn):
        if btn.isChecked():
            self.reset_tools(exclude_btn=btn)
            self.active_tool = "checkout"
            self.view.is_placing_checkout = True
            self.active_tool_params = {"type": c_type, "ori": ori}
            # DISABLE DRAG
            if self.view.sim_view:
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.reset_tools()

    def handle_scene_click(self, pos):
        if self.current_mode != "Editor":
            return
        if self.active_tool == "route":
            self.current_route_points.append(pos)
            dot = self.scene.addEllipse(
                pos.x() - 4,
                pos.y() - 4,
                8,
                8,
                QPen(COLOR_DARK_TEXT),
                QBrush(COLOR_ORANGE),
            )
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
            new_id = len(self.checkouts_data) + 1
            if self.checkouts_data:
                new_id = max(c["id"] for c in self.checkouts_data) + 1
            self.checkouts_data.append(
                {
                    "id": new_id,
                    "x": pos.x(),
                    "y": pos.y(),
                    "type": self.active_tool_params.get("type"),
                    "orientation": self.active_tool_params.get("ori"),
                    "open": True,
                    "skill": "Azubi",
                    "max_queue": 5,
                }
            )
            self.draw_debug_elements()

    def finish_route_drawing(self):
        if self.active_tool == "route" and self.current_route_points:
            name = f"Route_{len(self.all_routes)+1}"
            self.all_routes[name] = list(self.current_route_points)
            self.view.route_list_widget.addItem(name)
        self.reset_tools()

    def handle_waiting_area_created(self, rect):
        if self.active_tool == "waiting_area":
            self.waiting_area_rect = rect
            self.draw_debug_elements()
        elif self.active_tool == "start_area":
            self.start_area_rect = rect
            self.draw_debug_elements()

    def edit_selected_object(self):
        item = self.view.object_list_widget.currentItem()
        if not item:
            QMessageBox.information(
                self.view, "Info", "Bitte ein Objekt aus der Liste wählen."
            )
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        obj_type = data["type"]
        cx, cy, name = 0, 0, "Objekt"
        if obj_type == "shelf":
            idx = data["index"]
            if idx < len(self.all_shelves):
                pt = self.all_shelves[idx]
                cx, cy = pt.x(), pt.y()
                name = f"Regal #{idx+1}"
            else:
                return
        elif obj_type == "checkout":
            cid = data["id"]
            c_data = next(
                (c for c in self.checkouts_data if c["id"] == cid), None
            )
            if c_data:
                cx, cy = c_data["x"], c_data["y"]
                name = f"Kasse #{cid}"
            else:
                return
        dlg = ObjectPositionDialog(name, cx, cy, self.view)

        def on_chg(nx, ny):
            if obj_type == "shelf":
                idx = data["index"]
                if idx < len(self.all_shelves):
                    self.all_shelves[idx] = QPointF(nx, ny)
            elif obj_type == "checkout":
                cid = data["id"]
                c_data = next(
                    (c for c in self.checkouts_data if c["id"] == cid), None
                )
                if c_data:
                    c_data["x"] = nx
                    c_data["y"] = ny
            self.draw_debug_elements()

        dlg.position_changed.connect(on_chg)
        dlg.exec()
        self.draw_debug_elements()

    def delete_selected_object_from_list(self):
        item = self.view.object_list_widget.currentItem()
        if not item:
            QMessageBox.information(
                self.view, "Info", "Bitte ein Objekt aus der Liste wählen."
            )
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        obj_type = data["type"]
        if obj_type == "shelf":
            idx = data["index"]
            if idx < len(self.all_shelves):
                del self.all_shelves[idx]
        elif obj_type == "checkout":
            cid = data["id"]
            for i, c in enumerate(self.checkouts_data):
                if c["id"] == cid:
                    del self.checkouts_data[i]
                    break
        self.selected_object_spec = None
        self.draw_debug_elements()

    def delete_selected_route(self):
        item = self.view.route_list_widget.currentItem()
        if not item:
            return
        name = item.text()
        if name in self.all_routes:
            del self.all_routes[name]
        self.view.route_list_widget.takeItem(
            self.view.route_list_widget.row(item)
        )
        self.draw_debug_elements()

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

    def update_object_list(self):
        self.view.object_list_widget.clear()
        for c in self.checkouts_data:
            label = f"Kasse #{c.get('id')} ({c.get('type')})"
            item = QListWidgetItem(label)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "checkout", "id": c.get("id")},
            )
            self.view.object_list_widget.addItem(item)
        for idx, p in enumerate(self.all_shelves):
            label = f"Regal #{idx+1} ({int(p.x())}, {int(p.y())})"
            item = QListWidgetItem(label)
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "shelf", "index": idx}
            )
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
                    elif (
                        spec["type"] == "shelf" and d["index"] == spec["index"]
                    ):
                        self.view.object_list_widget.setCurrentRow(row)
                        break

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
        if (
            self.current_map_file is None
            or self.current_map_file.name != target_map
        ):
            self.load_map(target_map)

    def create_default_map(self):
        default_data = {
            "routes": {},
            "shelves": [],
            "checkouts": [],
            "waiting_area": None,
        }
        with open(MAPS_DIR / "default.json", "w") as f:
            json.dump(default_data, f, indent=4)

    def on_map_selection_changed(self, map_name):
        if map_name:
            self.load_map(map_name)

    def load_map(self, map_name):
        file_path = MAPS_DIR / map_name
        if not file_path.exists():
            return
        self.current_map_file = file_path
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            self.all_routes = {}
            if "routes" in data:
                for k, v in data["routes"].items():
                    self.all_routes[k] = [QPointF(p[0], p[1]) for p in v]

            raw_shelves = data.get("shelves", [])
            self.all_shelves = []
            for s in raw_shelves:
                if isinstance(s, dict):
                    self.all_shelves.append(QPointF(s["x"], s["y"]))
                elif isinstance(s, list):
                    self.all_shelves.append(QPointF(s[0], s[1]))

            self.checkouts_data = data.get("checkouts", [])
            self.waiting_area_rect = (
                QRectF(*data["waiting_area"])
                if data.get("waiting_area")
                else None
            )

            self.start_area_rect = (
                QRectF(*data["start_area"]) if data.get("start_area") else None
            )

            global_exit = data.get("global_exit_direction", "Rechts")
            self.view.combo_global_exit.setCurrentText(global_exit)

            self.update_object_list()
            self.view.route_list_widget.clear()
            for r in self.all_routes:
                self.view.route_list_widget.addItem(r)
            self.draw_debug_elements()
            self.on_mode_changed(self.current_mode)
            print(f"Loaded Map: {map_name}")
        except Exception as e:
            print(f"Error loading map: {e}")

    def save_current_map(self):
        if not self.current_map_file:
            return
        routes_export = {
            k: [[p.x(), p.y()] for p in v] for k, v in self.all_routes.items()
        }
        shelves_export = [[p.x(), p.y()] for p in self.all_shelves]

        wa_export = (
            [
                self.waiting_area_rect.x(),
                self.waiting_area_rect.y(),
                self.waiting_area_rect.width(),
                self.waiting_area_rect.height(),
            ]
            if self.waiting_area_rect
            else None
        )
        sa_export = (
            [
                self.start_area_rect.x(),
                self.start_area_rect.y(),
                self.start_area_rect.width(),
                self.start_area_rect.height(),
            ]
            if self.start_area_rect
            else None
        )

        global_exit = self.view.combo_global_exit.currentText()

        data = {
            "routes": routes_export,
            "shelves": shelves_export,
            "checkouts": self.checkouts_data,
            "waiting_area": wa_export,
            "start_area": sa_export,
            "global_exit_direction": global_exit,
        }
        try:
            with open(self.current_map_file, "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(
                self.view,
                "Gespeichert",
                f"Map '{self.current_map_file.name}' gespeichert.",
            )
        except Exception as e:
            QMessageBox.critical(self.view, "Fehler", f"Fehler: {e}")

    def create_new_map(self):
        name, ok = QInputDialog.getText(
            self.view, "Neue Map", "Name (ohne .json):"
        )
        if ok and name:
            if not name.endswith(".json"):
                name += ".json"
            path = MAPS_DIR / name
            with open(path, "w") as f:
                json.dump({"routes": {}, "shelves": [], "checkouts": []}, f)
            self.refresh_map_list()
            self.view.map_combo.setCurrentText(name)

    def delete_current_map(self):
        if (
            not self.current_map_file
            or self.current_map_file.name == "default.json"
        ):
            QMessageBox.warning(
                self.view,
                "Warnung",
                "Standard-Map kann nicht gelöscht werden.",
            )
            return
        reply = QMessageBox.question(
            self.view,
            "Löschen",
            f"'{self.current_map_file.name}' löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.current_map_file)
                self.current_map_file = None
                self.refresh_map_list()
            except Exception as e:
                QMessageBox.critical(
                    self.view, "Fehler", f"Löschen fehlgeschlagen: {e}"
                )

    def open_visibility_dialog(self):
        dlg = VisibilityDialog(self.settings, self.view)
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.draw_debug_elements()

    def open_offsets_dialog(self):
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
