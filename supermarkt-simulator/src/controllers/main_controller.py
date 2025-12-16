"""
Main controller module.
"""

import json
import random
from PyQt6.QtCore import QTimer, QPointF, Qt, QRectF
from PyQt6.QtGui import QPen, QBrush, QPainterPath, QVector2D
from PyQt6.QtWidgets import (
    QListWidgetItem,
    QGraphicsPathItem,
    QTableWidgetItem,
    QCheckBox,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
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
from views.dialogs import SettingsDialog, ObjectPositionDialog


class MainController:
    """
    The central controller connecting Models and Views.

    Manages the simulation lifecycle, data persistence, user interaction events,
    and admin mode logic.
    """

    def __init__(self):
        """
        Initializes the controller, loads data, and sets up view connections.
        """
        # MODELS & DATA
        self.all_routes = {}
        self.all_shelves = []
        self.checkouts_data = []
        self.waiting_area_rect = None
        self.settings = DEFAULT_SETTINGS.copy()

        self.routes_file = BASE_DIR / "routes.json"
        self.shelves_file = BASE_DIR / "shelves.json"
        self.checkouts_file = BASE_DIR / "checkouts.json"
        self.waiting_area_file = BASE_DIR / "waiting_area.json"
        self.settings_file = BASE_DIR / "settings.json"

        # SIM STATE
        self.customers_model = []  # List of CustomerModel Objects
        self.customer_items = []  # List of CustomerItem Objects
        self.checkout_queues = {}  # {id: [CustomerModel, ...]}
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

        # Connections
        self.view.start_sim_button.clicked.connect(self.toggle_simulation)
        self.view.settings_button.clicked.connect(self.open_settings_dialog)
        self.view.new_route_button.clicked.connect(self.start_drawing_mode)
        self.view.place_shelves_button.clicked.connect(self.start_shelf_mode)
        self.view.waiting_area_button.clicked.connect(
            self.start_waiting_area_mode
        )
        self.view.btn_save_admin.clicked.connect(self.finish_admin_action)
        self.view.btn_cancel_admin.clicked.connect(self.cancel_admin_action)

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

        # List interactions
        self.view.route_list_widget.itemClicked.connect(
            lambda i: None
        )  # Placeholder
        self.view.object_list_widget.itemClicked.connect(
            self.on_object_list_clicked
        )
        self.view.btn_del_route.clicked.connect(self.delete_selected_route)
        self.view.btn_edit_obj.clicked.connect(self.edit_selected_object)
        self.view.btn_del_obj.clicked.connect(
            self.delete_selected_object_from_list
        )

        self.scene.selectionChanged.connect(self.on_scene_selection_changed)

        self.load_settings()
        self.load_data()

    def show(self):
        """Displays the main window."""
        self.view.show()

    # --- SIMULATION LOOP ---
    def toggle_simulation(self):
        """Starts or stops the simulation loop."""
        if self.sim_timer.isActive():
            self.sim_timer.stop()
            self.view.start_sim_button.setText("Start")
        else:
            self.start_simulation()

    def start_simulation(self):
        """
        Initializes and starts the simulation.
        Creates models and visuals for customers.
        """
        if not self.all_routes:
            return
        count = self.view.actor_count_input.value()
        route_names = list(self.all_routes.keys())

        # Clear Old
        for c in self.customer_items:
            self.scene.removeItem(c)
        self.customers_model.clear()
        self.customer_items.clear()
        self.checkout_queues = {}
        self.queue_count = 0

        self.draw_debug_elements()

        for _ in range(count):
            r_name = random.choice(route_names)
            # Create Model
            model = CustomerModel(
                self.all_routes[r_name],
                self.all_shelves,
                self.waiting_area_rect,
            )
            self.customers_model.append(model)
            # Create View
            item = CustomerItem(model)
            self.scene.addItem(item)
            self.customer_items.append(item)

        self.view.start_sim_button.setText("Stop")
        self.sim_timer.start(SIM_TICK_MS)

    def simulation_tick(self):
        """
        Executed on every simulation tick.
        Updates model logic and syncs visual items.
        """
        active_models = []
        active_items = []
        waiting_cnt = 0

        for i, model in enumerate(self.customers_model):
            item = self.customer_items[i]

            model.tick()  # Data manipulation
            item.sync_visuals()  # Sync View to Model

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
                    dist = (
                        QVector2D(model.pos) - QVector2D(model.target_pos)
                    ).length()
                    if dist < 5.0:
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
        """
        Attempts to assign a customer to a checkout queue.

        @param model: The customer model.
        """
        candidates = []
        for c_data in self.checkouts_data:
            if not c_data.get("open", True):
                continue
            cid = c_data["id"]
            max_q = c_data.get("max_queue", 5)
            current_q = self.checkout_queues.get(cid, [])
            if len(current_q) < max_q:
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
        """
        Moves customers forward in the specified queue.

        @param cid: Checkout ID.
        """
        if cid not in self.checkout_queues:
            return
        for idx, model in enumerate(self.checkout_queues[cid]):
            self.set_queue_target(model, cid, idx)
            if model.state != "SCANNING":
                model.state = "IN_QUEUE"

    def set_queue_target(self, model, cid, q_index):
        """
        Calculates the physical position for a customer in a queue.

        @param model: The customer model.
        @param cid: Checkout ID.
        @param q_index: Index in the queue.
        """
        c_data = next((x for x in self.checkouts_data if x["id"] == cid), None)
        if not c_data:
            return
        cx, cy = c_data["x"], c_data["y"]
        ori = c_data.get("orientation", "Right")
        c_type = c_data["type"]

        offset_key = "offset_queue_"
        if c_type == "SB":
            offset_key += "sb_"
        offset_key += "left" if ori == "Left" else "right"

        off = self.settings[offset_key]
        sx = cx + off[0]
        sy = cy + off[1]
        target = QPointF(sx, sy + (q_index * QUEUE_SPACING))
        model.go_to_queue(target, cid)

    # --- DATA MANAGEMENT ---
    def load_data(self):
        """Loads all JSON data files."""

        def load_json(p):
            if p.exists():
                with open(p, "r") as f:
                    return json.load(f)
            return None

        rd = load_json(self.routes_file)
        if rd:
            self.all_routes = {
                k: [QPointF(p[0], p[1]) for p in v] for k, v in rd.items()
            }
            for n in self.all_routes:
                self.view.route_list_widget.addItem(n)

        sd = load_json(self.shelves_file)
        if sd:
            self.all_shelves = [QPointF(p[0], p[1]) for p in sd]

        cd = load_json(self.checkouts_file)
        if cd:
            self.checkouts_data = cd

        wd = load_json(self.waiting_area_file)
        if wd:
            self.waiting_area_rect = QRectF(*wd)

        self.update_checkout_table()
        self.draw_debug_elements()
        self.update_object_list()

    def save_data_generic(self, fp, d):
        """Generic JSON save helper."""
        with open(fp, "w") as f:
            json.dump(d, f)

    def update_checkout_table(self):
        """Refreshes the checkout configuration table in the UI."""
        t = self.view.checkout_table
        t.setRowCount(len(self.checkouts_data))
        for i, c_data in enumerate(self.checkouts_data):
            t.setItem(i, 0, QTableWidgetItem(str(c_data.get("id", i + 1))))
            t.setItem(
                i,
                1,
                QTableWidgetItem(
                    f"{c_data['type']} ({c_data.get('orientation','R')})"
                ),
            )

            chk = QCheckBox()
            chk.setChecked(c_data["open"])
            chk.toggled.connect(
                lambda checked, idx=i: self.on_checkout_status_changed(
                    idx, checked
                )
            )
            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(chk)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)
            t.setCellWidget(i, 2, w)

            if c_data["type"] == "Normal":
                cb = QComboBox()
                cb.addItems(["Azubi", "Erfahren", "Profi"])
                cb.setCurrentText(c_data.get("skill", "Azubi"))
                cb.currentTextChanged.connect(
                    lambda txt, idx=i: self.on_checkout_skill_changed(idx, txt)
                )
                t.setCellWidget(i, 3, cb)
            else:
                t.setItem(i, 3, QTableWidgetItem("-"))

            sb = QSpinBox()
            sb.setRange(1, 50)
            sb.setValue(c_data.get("max_queue", 5))
            sb.valueChanged.connect(
                lambda v, idx=i: self.on_checkout_max_queue_changed(idx, v)
            )
            t.setCellWidget(i, 4, sb)

    def on_checkout_status_changed(self, idx, val):
        """Handles checkout open/close toggle."""
        self.checkouts_data[idx]["open"] = val
        self.save_data_generic(self.checkouts_file, self.checkouts_data)
        self.draw_debug_elements()

    def on_checkout_skill_changed(self, idx, val):
        """Handles checkout skill change."""
        self.checkouts_data[idx]["skill"] = val
        self.save_data_generic(self.checkouts_file, self.checkouts_data)

    def on_checkout_max_queue_changed(self, idx, val):
        """Handles checkout max queue change."""
        self.checkouts_data[idx]["max_queue"] = val
        self.save_data_generic(self.checkouts_file, self.checkouts_data)

    def draw_debug_elements(self):
        """
        Refreshes the static elements in the scene (Shelves, Checkouts, Routes, Waiting Area).
        """
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
                s = ShelfItem(p.x(), p.y())
                self.scene.addItem(s)
                self.shelf_items.append(s)

        # Checkouts & Cashiers & Route Debug
        for i in self.checkout_items:
            self.scene.removeItem(i)
        for i in self.cashier_items:
            self.scene.removeItem(i)
        for i in self.route_debug_items:
            self.scene.removeItem(i)
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()

        if self.settings["show_checkouts"]:
            for cd in self.checkouts_data:
                # Light Offset Logic
                ori = cd.get("orientation", "Right")
                c_type = cd["type"]
                lo = (
                    (
                        self.settings["offset_light_sb_left"]
                        if ori == "Left"
                        else self.settings["offset_light_sb_right"]
                    )
                    if c_type == "SB"
                    else (
                        self.settings["offset_light_normal_left"]
                        if ori == "Left"
                        else self.settings["offset_light_normal_right"]
                    )
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
                self.scene.addItem(ci)
                self.checkout_items.append(ci)

                # Queue Lines
                if self.settings["show_routes"] or self.view.highlight_queues:
                    off_key = (
                        "offset_queue_sb_"
                        if c_type == "SB"
                        else "offset_queue_"
                    )
                    off_key += "left" if ori == "Left" else "right"
                    off = self.settings[off_key]
                    sx = cd["x"] + off[0]
                    sy = cd["y"] + off[1]
                    pp = QPainterPath()
                    pp.moveTo(sx, sy)
                    pp.lineTo(sx, sy + 60)
                    pen = (
                        QPen(COLOR_QUEUE_HIGHLIGHT, 3)
                        if self.view.highlight_queues
                        else QPen(
                            QColor(200, 0, 0, 100), 2, Qt.PenStyle.DashLine
                        )
                    )
                    li = QGraphicsPathItem(pp)
                    li.setPen(pen)
                    self.scene.addItem(li)
                    self.route_debug_items.append(li)

                # Cashiers
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

        # Routes
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

    def update_object_list(self):
        """Updates the list of objects in the management tab."""
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

    # --- ADMIN INTERACTION ---
    def toggle_admin_mode_logic(self, active):
        """
        Handles admin mode state changes from the Controller side.
        @param active: Is admin mode active?
        """
        if not active:
            self.cancel_admin_action()
        self.draw_debug_elements()

    def setup_admin_fullscreen(self, title):
        """Configures the UI for a specific admin task (fullscreen editor)."""
        self.view.top_row_widget.hide()
        self.view.bottom_right_group_box.hide()
        self.view.admin_toolbar.show()
        self.view.bottom_left_group_box.setTitle(f"Editor: {title}")
        self.view.bottom_left_group_box.setEnabled(True)

    def start_drawing_mode(self):
        """Starts route drawing mode."""
        self.view.is_drawing_mode = True
        self.setup_admin_fullscreen("Route zeichnen")
        self.current_route_points = []
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(
            QPen(COLOR_ORANGE, 3, Qt.PenStyle.DashLine)
        )
        self.scene.addItem(self.current_route_path_item)

    def start_shelf_mode(self):
        """Starts shelf placement mode."""
        self.view.is_placing_shelves = True
        self.setup_admin_fullscreen("Regale platzieren")
        self.draw_debug_elements()

    def start_waiting_area_mode(self):
        """Starts waiting area drawing mode."""
        self.view.is_drawing_waiting_area = True
        self.setup_admin_fullscreen("Wartebereich ziehen")
        if self.waiting_area_item:
            self.waiting_area_item.setVisible(True)

    def start_checkout_mode(self, c_type, ori):
        """
        Starts checkout placement mode.
        @param c_type: Checkout type.
        @param ori: Orientation.
        """
        self.view.is_placing_checkout = True
        self.view.current_checkout_type = c_type
        self.view.current_checkout_orientation = ori
        self.setup_admin_fullscreen(f"Kasse ({c_type}-{ori})")

    def handle_scene_click(self, pos):
        """
        Handles click events from the scene (adding points/objects).
        @param pos: Scene position clicked.
        """
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
            s = ShelfItem(pos.x(), pos.y())
            self.scene.addItem(s)
            self.shelf_items.append(s)
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
                    "skill": (
                        "Azubi"
                        if self.view.current_checkout_type == "Normal"
                        else None
                    ),
                    "max_queue": 5,
                }
            )
            self.save_data_generic(self.checkouts_file, self.checkouts_data)
            self.draw_debug_elements()
            self.update_checkout_table()
            self.update_object_list()

    def handle_waiting_area_created(self, rect):
        """Handles creation of the waiting area rectangle."""
        self.waiting_area_rect = rect
        self.draw_debug_elements()

    def finish_admin_action(self):
        """Saves current admin action results to JSON."""
        if self.view.is_drawing_mode and self.current_route_points:
            name = f"Route_{len(self.all_routes)+1}"
            self.all_routes[name] = list(self.current_route_points)
            d = {
                k: [[p.x(), p.y()] for p in v]
                for k, v in self.all_routes.items()
            }
            self.save_data_generic(self.routes_file, d)
            self.view.route_list_widget.addItem(name)
        elif self.view.is_placing_shelves:
            self.save_data_generic(
                self.shelves_file, [[p.x(), p.y()] for p in self.all_shelves]
            )
        elif self.view.is_drawing_waiting_area and self.waiting_area_rect:
            d = [
                self.waiting_area_rect.x(),
                self.waiting_area_rect.y(),
                self.waiting_area_rect.width(),
                self.waiting_area_rect.height(),
            ]
            self.save_data_generic(self.waiting_area_file, d)
        self.cancel_admin_action()

    def cancel_admin_action(self):
        """Cancels current admin mode and resets UI."""
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
        self.view.top_row_widget.show()
        self.view.bottom_right_group_box.show()
        self.view.bottom_left_group_box.setTitle("Routen-Editor")
        self.view.bottom_left_group_box.setEnabled(False)
        self.draw_debug_elements()

    # --- EDITING ---
    def delete_selected_route(self):
        """Deletes the selected route."""
        sel = self.view.route_list_widget.selectedItems()
        if not sel:
            return
        name = sel[0].text()
        del self.all_routes[name]
        self.view.route_list_widget.takeItem(
            self.view.route_list_widget.row(sel[0])
        )
        d = {
            k: [[p.x(), p.y()] for p in v] for k, v in self.all_routes.items()
        }
        self.save_data_generic(self.routes_file, d)
        self.draw_debug_elements()

    def open_settings_dialog(self):
        """Opens the settings dialog."""
        was_max = self.view.is_sim_maximized
        if not was_max:
            self.view.toggle_simulation_fullscreen(force=True)
        self.view.highlight_queues = True
        self.draw_debug_elements()

        dlg = SettingsDialog(self.settings, self.view)
        dlg.settings_changed.connect(self.apply_live_settings)
        dlg.exec()

        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

        self.view.highlight_queues = False
        self.draw_debug_elements()
        if not was_max:
            self.view.toggle_simulation_fullscreen(force=True)

    def apply_live_settings(self, ns):
        """Applies settings in real-time."""
        self.settings = ns
        self.draw_debug_elements()

    def load_settings(self):
        """Loads settings from disk."""
        if self.settings_file.exists():
            with open(self.settings_file, "r") as f:
                self.settings.update(json.load(f))

    def on_object_list_clicked(self, item):
        """Handles object selection from list."""
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
        """Syncs scene selection back to the list widget."""
        sel = self.scene.selectedItems()
        if not sel:
            return
        # Logic to highlight item in list could be added here
        pass

    def edit_selected_object(self):
        """Opens position editor for selected object."""
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

        was_max = self.view.is_sim_maximized
        if not was_max:
            self.view.toggle_simulation_fullscreen(force=True)

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
                    self.save_data_generic(
                        self.shelves_file,
                        [[p.x(), p.y()] for p in self.all_shelves],
                    )
                    self.draw_debug_elements()
            elif isinstance(it, CheckoutItem):
                for c in self.checkouts_data:
                    if c["id"] == it.data_id:
                        c["x"] = nx
                        c["y"] = ny
                        self.save_data_generic(
                            self.checkouts_file, self.checkouts_data
                        )
                        self.draw_debug_elements()
                        break

        dlg.position_changed.connect(on_chg)
        dlg.exec()
        if not was_max:
            self.view.toggle_simulation_fullscreen(force=True)
        self.update_object_list()

    def delete_selected_object_from_list(self):
        """Deletes selected object."""
        sel = self.scene.selectedItems()
        if not sel:
            return
        it = sel[0]

        if isinstance(it, ShelfItem):
            try:
                idx = self.shelf_items.index(it)
                del self.all_shelves[idx]
                self.save_data_generic(
                    self.shelves_file,
                    [[p.x(), p.y()] for p in self.all_shelves],
                )
            except:
                pass
        elif isinstance(it, CheckoutItem):
            for i, c in enumerate(self.checkouts_data):
                if c["id"] == it.data_id:
                    del self.checkouts_data[i]
                    self.save_data_generic(
                        self.checkouts_file, self.checkouts_data
                    )
                    self.update_checkout_table()
                    break

        self.draw_debug_elements()
        self.update_object_list()
