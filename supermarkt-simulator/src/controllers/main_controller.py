"""
Main controller module orchestrating the simulation and map management.
Refactored: Implemented separate handlers for Visibility and Offset dialogs.
"""

import json
import random
import os
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QVector2D, QPainterPath, QColor
from PyQt6.QtWidgets import (
    QListWidgetItem,
    QGraphicsPathItem,
    QMessageBox,
    QInputDialog,
)

from config import *
from views.main_window import MainWindow
from models.customer import CustomerModel
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
)
from views.dialogs import (
    VisibilityDialog,  # New class
    OffsetDialog,  # New class
    ObjectPositionDialog,
    CheckoutConfigDialog,
)


class MainController:
    """
    The central controller class connecting Models, Views, and Data logic.
    """

    def __init__(self):
        # MODELS & DATA
        self.all_routes = {}
        self.all_shelves = []
        self.checkouts_data = []
        self.waiting_area_rect = None
        self.settings = DEFAULT_SETTINGS.copy()

        # Map System
        self.current_map_file = None
        if not MAPS_DIR.exists():
            os.makedirs(MAPS_DIR)

        self.settings_file = BASE_DIR / "settings.json"

        # SIM STATE
        self.customers_model = []
        self.customer_items = []
        self.checkout_queues = {}
        self.queue_count = 0
        self.shelf_items = []
        self.checkout_items = []
        self.route_debug_items = []
        self.cashier_items = []
        self.waiting_area_item = None

        self.current_route_points = []
        self.current_route_path_item = None
        self.current_route_point_items = []

        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulation_tick)

        # VIEW
        self.view = MainWindow()
        self.view.set_controller(self)
        self.scene = self.view.sim_scene

        # --- CONNECTIONS ---

        # 1. Top Toolbar
        self.view.start_sim_button.clicked.connect(self.toggle_simulation)
        self.view.btn_reset_zoom.clicked.connect(self.view.reset_sim_zoom)
        self.view.map_combo.currentTextChanged.connect(
            self.on_map_selection_changed
        )

        # 2. Tabs Logic
        self.view.control_tabs.currentChanged.connect(self.on_tab_changed)

        # 3. Editor Tools (Tab 2)
        self.view.btn_new_map.clicked.connect(self.create_new_map)
        self.view.btn_save_map.clicked.connect(self.save_current_map)
        self.view.btn_delete_map.clicked.connect(self.delete_current_map)

        self.view.new_route_button.clicked.connect(self.start_drawing_mode)
        self.view.place_shelves_button.clicked.connect(self.start_shelf_mode)
        self.view.waiting_area_button.clicked.connect(
            self.start_waiting_area_mode
        )

        # CHANGED: Connect separate buttons
        self.view.btn_visibility.clicked.connect(self.open_visibility_dialog)
        self.view.btn_offsets.clicked.connect(self.open_offsets_dialog)

        # Editor Action Bar
        self.view.btn_save_admin.clicked.connect(self.finish_admin_action)
        self.view.btn_cancel_admin.clicked.connect(self.cancel_admin_action)

        # Checkout Buttons
        self.view.btn_kl.clicked.connect(
            lambda: self.start_checkout_mode("Normal", "Left")
        )
        self.view.btn_kr.clicked.connect(
            lambda: self.start_checkout_mode("Normal", "Right")
        )
        self.view.btn_sl.clicked.connect(
            lambda: self.start_checkout_mode("SB", "Left")
        )
        self.view.btn_sr.clicked.connect(
            lambda: self.start_checkout_mode("SB", "Right")
        )

        # 4. Data Lists
        self.view.route_list_widget.itemClicked.connect(lambda i: None)
        self.view.object_list_widget.itemClicked.connect(
            self.on_object_list_clicked
        )
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.btn_edit_obj.clicked.connect(self.edit_selected_object)
        self.view.btn_del_obj.clicked.connect(
            self.delete_selected_object_from_list
        )

        # 5. Scene Interactions
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.scene.clicked_point.connect(self.handle_scene_click)
        self.scene.waiting_area_created.connect(
            self.handle_waiting_area_created
        )

        # Initial Load
        self.load_settings()
        self.refresh_map_list()

    def show(self):
        self.view.show()

    # --- TABS ---
    def on_tab_changed(self, index):
        is_editor = index == 1
        self.view.is_admin_mode = is_editor
        if not is_editor:
            self.cancel_admin_action()
            self.draw_debug_elements()

    # --- MAP SYSTEM ---
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

            self.all_shelves = [
                QPointF(p[0], p[1]) for p in data.get("shelves", [])
            ]
            self.checkouts_data = data.get("checkouts", [])
            self.waiting_area_rect = (
                QRectF(*data["waiting_area"])
                if data.get("waiting_area")
                else None
            )

            self.update_object_list()
            self.view.route_list_widget.clear()
            for r in self.all_routes:
                self.view.route_list_widget.addItem(r)

            self.draw_debug_elements()
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

        data = {
            "routes": routes_export,
            "shelves": shelves_export,
            "checkouts": self.checkouts_data,
            "waiting_area": wa_export,
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

    # --- SIMULATION ---
    def toggle_simulation(self):
        if self.sim_timer.isActive():
            self.sim_timer.stop()
            self.view.start_sim_button.setText("▶ Simulation Fortsetzen")
            self.view.start_sim_button.setStyleSheet(
                f"background-color: {COLOR_SUCCESS.name()}; color: white; font-weight: bold; font-size: 14px; padding: 6px; border-radius: 4px;"
            )
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.all_routes:
            QMessageBox.warning(
                self.view, "Warnung", "Keine Routen definiert!"
            )
            return

        count = self.view.actor_count_input.value()
        route_names = list(self.all_routes.keys())

        for c in self.customer_items:
            self.scene.removeItem(c)
        self.customers_model.clear()
        self.customer_items.clear()
        self.checkout_queues = {}
        self.queue_count = 0

        self.draw_debug_elements()

        for _ in range(count):
            r_name = random.choice(route_names)
            model = CustomerModel(
                self.all_routes[r_name],
                self.all_shelves,
                self.waiting_area_rect,
            )
            self.customers_model.append(model)
            item = CustomerItem(model)
            self.scene.addItem(item)
            self.customer_items.append(item)

        self.view.start_sim_button.setText("⏹ Stop Simulation")
        self.view.start_sim_button.setStyleSheet(
            f"background-color: {COLOR_WARNING.name()}; color: white; font-weight: bold; font-size: 14px; padding: 6px; border-radius: 4px;"
        )
        self.sim_timer.start(SIM_TICK_MS)

    def simulation_tick(self):
        active_models = []
        active_items = []
        waiting_cnt = 0
        for i, model in enumerate(self.customers_model):
            item = self.customer_items[i]
            model.tick()
            item.sync_visuals()

            if model.state == "FINISHED_SHOPPING":
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
                self.scene.removeItem(item)
            else:
                active_models.append(model)
                active_items.append(item)

        self.customers_model = active_models
        self.customer_items = active_items
        self.view.lbl_queue_count.setText(str(waiting_cnt))

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
        model.go_to_queue(target, cid)

    # --- ADMIN / EDITOR ---
    def start_drawing_mode(self):
        self.view.is_drawing_mode = True
        self.view.admin_toolbar.show()
        self.current_route_points = []
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(
            QPen(COLOR_ORANGE, 3, Qt.PenStyle.DashLine)
        )
        self.scene.addItem(self.current_route_path_item)

    def start_shelf_mode(self):
        self.view.is_placing_shelves = True
        self.view.admin_toolbar.show()
        self.draw_debug_elements()

    def start_waiting_area_mode(self):
        self.view.is_drawing_waiting_area = True
        self.view.admin_toolbar.show()
        if self.waiting_area_item:
            self.waiting_area_item.setVisible(True)

    def start_checkout_mode(self, c_type, ori):
        self.view.is_placing_checkout = True
        self.view.current_checkout_type = c_type
        self.view.current_checkout_orientation = ori
        self.view.admin_toolbar.show()

    def handle_scene_click(self, pos):
        if self.view.is_drawing_mode:
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
        elif self.view.is_placing_shelves:
            self.all_shelves.append(pos)
            self.scene.addItem(ShelfItem(pos.x(), pos.y()))
            self.update_object_list()
        elif self.view.is_placing_checkout:
            new_id = len(self.checkouts_data) + 1
            self.checkouts_data.append(
                {
                    "id": new_id,
                    "x": pos.x(),
                    "y": pos.y(),
                    "type": self.view.current_checkout_type,
                    "orientation": self.view.current_checkout_orientation,
                    "open": True,
                    "skill": "Azubi",
                    "max_queue": 5,
                }
            )
            self.draw_debug_elements()
            self.update_object_list()

    def on_checkout_clicked(self, checkout_id):
        """
        Slot to handle clicks on checkout items. Opens configuration dialog.
        """
        c_data = next(
            (x for x in self.checkouts_data if x["id"] == checkout_id), None
        )
        if not c_data:
            return

        dlg = CheckoutConfigDialog(c_data, self.view)
        if dlg.exec():
            # Update data from dialog
            c_data.update(dlg.get_data())
            # Refresh view
            self.draw_debug_elements()
            self.update_object_list()

    def handle_waiting_area_created(self, rect):
        self.waiting_area_rect = rect
        self.draw_debug_elements()

    def finish_admin_action(self):
        if self.view.is_drawing_mode and self.current_route_points:
            name = f"Route_{len(self.all_routes)+1}"
            self.all_routes[name] = list(self.current_route_points)
            self.view.route_list_widget.addItem(name)
        self.cancel_admin_action()

    def cancel_admin_action(self):
        self.view.is_drawing_mode = False
        self.view.is_placing_shelves = False
        self.view.is_drawing_waiting_area = False
        self.view.is_placing_checkout = False

        if self.current_route_path_item:
            self.scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for i in self.current_route_point_items:
            self.scene.removeItem(i)
        self.current_route_point_items.clear()

        self.view.admin_toolbar.hide()
        self.draw_debug_elements()

    # --- HELPERS ---

    # NEW: Open Visibility Dialog
    def open_visibility_dialog(self):
        dlg = VisibilityDialog(self.settings, self.view)
        # Connect live update signal
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()
        # Save on close
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.draw_debug_elements()

    # NEW: Open Offsets Dialog
    def open_offsets_dialog(self):
        self.view.highlight_queues = True
        self.draw_debug_elements()

        dlg = OffsetDialog(self.settings, self.view)
        # Connect live update signal
        dlg.settings_changed.connect(
            lambda ns: (self.settings.update(ns), self.draw_debug_elements())
        )
        dlg.exec()

        # Save on close
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

        self.view.highlight_queues = False
        self.draw_debug_elements()

    def load_settings(self):
        if self.settings_file.exists():
            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))

    def on_object_list_clicked(self, item):
        d = item.data(Qt.ItemDataRole.UserRole)
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

    def on_scene_selection_changed(self):
        pass

    def edit_selected_object(self):
        sel = self.scene.selectedItems()
        if not sel:
            return
        it = sel[0]
        cx, cy, name = 0, 0, "Unbekannt"
        if isinstance(it, ShelfItem):
            cx = it.rect().x() + SHELF_SIZE / 2
            cy = it.rect().y() + SHELF_SIZE / 2
            name = "Regal"
        elif isinstance(it, CheckoutItem):
            cx = it.pos().x()
            cy = it.pos().y()
            name = f"Kasse #{it.data_id}"

        dlg = ObjectPositionDialog(name, cx, cy, self.view)

        def on_chg(nx, ny):
            if isinstance(it, ShelfItem):
                best_i, min_d = -1, 9999
                for i, pos in enumerate(self.all_shelves):
                    d = (pos - QPointF(cx, cy)).manhattanLength()
                    if d < min_d:
                        min_d = d
                        best_i = i
                if best_i != -1:
                    self.all_shelves[best_i] = QPointF(nx, ny)
            elif isinstance(it, CheckoutItem):
                for c in self.checkouts_data:
                    if c["id"] == it.data_id:
                        c["x"] = nx
                        c["y"] = ny
                        break
            self.draw_debug_elements()

        dlg.position_changed.connect(on_chg)
        dlg.exec()
        self.update_object_list()

    def delete_selected_object_from_list(self):
        sel = self.scene.selectedItems()
        if not sel:
            return
        it = sel[0]
        if isinstance(it, ShelfItem):
            try:
                idx = self.shelf_items.index(it)
                del self.all_shelves[idx]
            except:
                pass
        elif isinstance(it, CheckoutItem):
            for i, c in enumerate(self.checkouts_data):
                if c["id"] == it.data_id:
                    del self.checkouts_data[i]
                    break
        self.draw_debug_elements()
        self.update_object_list()

    def delete_selected_route(self):
        sel = self.view.route_list_widget.selectedItems()
        if not sel:
            return
        name = sel[0].text()
        del self.all_routes[name]
        self.view.route_list_widget.takeItem(
            self.view.route_list_widget.row(sel[0])
        )
        self.draw_debug_elements()

    def update_object_list(self):
        self.view.object_list_widget.clear()
        for c in self.checkouts_data:
            i = QListWidgetItem(f"Kasse #{c.get('id')} ({c.get('type')})")
            i.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "checkout", "id": c.get("id")},
            )
            self.view.object_list_widget.addItem(i)
        for idx, p in enumerate(self.all_shelves):
            i = QListWidgetItem(f"Regal #{idx+1} ({int(p.x())}, {int(p.y())})")
            i.setData(
                Qt.ItemDataRole.UserRole, {"type": "shelf", "index": idx}
            )
            self.view.object_list_widget.addItem(i)

    def draw_debug_elements(self):
        # Waiting Area
        if self.waiting_area_item:
            self.scene.removeItem(self.waiting_area_item)
        if self.waiting_area_rect and self.settings.get(
            "show_waiting_area", True
        ):
            self.waiting_area_item = WaitingAreaItem(self.waiting_area_rect)
            self.scene.addItem(self.waiting_area_item)

        # Shelves
        for i in self.shelf_items:
            self.scene.removeItem(i)
        self.shelf_items.clear()
        if self.settings["show_shelves"] or self.view.is_placing_shelves:
            for p in self.all_shelves:
                self.scene.addItem(s := ShelfItem(p.x(), p.y()))
                self.shelf_items.append(s)

        # Checkouts & Cashiers
        for i in (
            self.checkout_items + self.cashier_items + self.route_debug_items
        ):
            self.scene.removeItem(i)
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()

        if self.settings["show_checkouts"]:
            for cd in self.checkouts_data:
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

                # SIGNAL VERBINDEN
                ci.clicked.connect(self.on_checkout_clicked)

                self.scene.addItem(ci)
                self.checkout_items.append(ci)

                # Routes
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
        self.update_object_list()
