import sys
import json
import random
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
    QComboBox,
    QCheckBox,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QGraphicsPathItem,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPen, QBrush, QPixmap, QPainterPath

import pyqtgraph as pg

# Eigene Module importieren
from config import *
from items import (
    CheckoutItem,
    ShelfItem,
    WaitingAreaItem,
    CashierItem,
    CustomerItem,
)
from dialogs import ObjectPositionDialog, SettingsDialog
from ui_components import (
    ClickableGroupBox,
    ClickablePixmapItem,
    AutoFitGraphicsView,
    RouteEditorScene,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototyp 18: Refactoring (Projekt: Piep)")
        self.setGeometry(100, 100, 1400, 900)

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
        self.is_deleting_objects = False

        self.routes_file = BASE_DIR / "routes.json"
        self.shelves_file = BASE_DIR / "shelves.json"
        self.checkouts_file = BASE_DIR / "checkouts.json"
        self.waiting_area_file = BASE_DIR / "waiting_area.json"
        self.settings_file = BASE_DIR / "settings.json"
        self.settings = DEFAULT_SETTINGS.copy()

        self.all_routes = {}
        self.all_shelves = []
        self.checkouts_data = []
        self.waiting_area_rect = None
        self.current_route_points = []

        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulation_tick)
        self.customers = []
        self.cashier_items = []
        self.queue_count = 0
        self.checkout_queues = {}
        self.item_q1 = None
        self.item_q2 = None
        self.item_q3 = None
        self.item_q4 = None
        self.current_route_path_item = None
        self.current_route_point_items = []
        self.shelf_items = []
        self.checkout_items = []
        self.waiting_area_item = None
        self.route_debug_items = []
        self.scene_rect = QRectF()

        self.setup_ui()
        self.load_settings()
        self.load_data()
        self.sim_scene.selectionChanged.connect(
            self.on_scene_selection_changed
        )

    def setup_ui(self):
        w = QWidget()
        self.setCentralWidget(w)
        ml = QVBoxLayout(w)
        ml.setSpacing(10)
        ml.setContentsMargins(10, 10, 10, 10)
        self.top_row_widget = QWidget()
        tr = QHBoxLayout(self.top_row_widget)
        tr.setContentsMargins(0, 0, 0, 0)
        self.top_left_group_box = self.create_top_left_quadrant()
        self.top_right_group_box = self.create_top_right_quadrant()
        tr.addWidget(self.top_left_group_box, 1)
        tr.addWidget(self.top_right_group_box, 1)
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
        gb = QGroupBox("Eingabeparameter")
        l = QVBoxLayout(gb)
        l.setContentsMargins(5, 5, 5, 5)
        l.setSpacing(10)
        self.admin_mode_checkbox = QCheckBox("Admin-Modus")
        self.admin_mode_checkbox.toggled.connect(self.toggle_admin_mode)
        l.addWidget(self.admin_mode_checkbox)
        self.top_left_stack = QStackedWidget()
        l.addWidget(self.top_left_stack)

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
        self.start_sim_button.clicked.connect(self.toggle_simulation)
        sl.addWidget(self.start_sim_button)

        adm_w = QWidget()
        al = QVBoxLayout(adm_w)
        self.settings_button = QPushButton("Layout anpassen...")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.new_route_button = QPushButton("Route zeichnen")
        self.new_route_button.clicked.connect(self.start_drawing_mode)
        self.place_shelves_button = QPushButton("Regale platzieren")
        self.place_shelves_button.clicked.connect(self.start_shelf_mode)
        self.waiting_area_button = QPushButton("Wartebereich")
        self.waiting_area_button.clicked.connect(self.start_waiting_area_mode)

        cl = QHBoxLayout()
        bnl = QPushButton("K(L)")
        bnr = QPushButton("K(R)")
        bsl = QPushButton("SB(L)")
        bsr = QPushButton("SB(R)")
        bnl.clicked.connect(lambda: self.start_checkout_mode("Normal", "Left"))
        bnr.clicked.connect(
            lambda: self.start_checkout_mode("Normal", "Right")
        )
        bsl.clicked.connect(lambda: self.start_checkout_mode("SB", "Left"))
        bsr.clicked.connect(lambda: self.start_checkout_mode("SB", "Right"))
        cl.addWidget(bnl)
        cl.addWidget(bnr)
        cl.addWidget(bsl)
        cl.addWidget(bsr)

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
        bs = QPushButton("Speichern")
        bs.clicked.connect(self.finish_admin_action)
        bc = QPushButton("Abbrechen")
        bc.clicked.connect(self.cancel_admin_action)
        tl.addWidget(bs)
        tl.addWidget(bc)
        l.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        self.sim_scene = RouteEditorScene()
        self.sim_scene.main_window = self  # WICHTIG: Referenz setzen
        self.sim_scene.clicked_point.connect(self.handle_scene_click)
        self.sim_scene.waiting_area_created.connect(
            self.handle_waiting_area_created
        )
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        l.addWidget(self.sim_view)

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
        except Exception as e:
            print(f"Warning loading assets: {e}")
        return gb

    def create_bottom_right_quadrant(self):
        gb = QGroupBox("Verwaltung")
        self.bottom_right_stack = QStackedWidget(gb)
        l = QVBoxLayout(gb)
        l.addWidget(self.bottom_right_stack)
        self.bottom_right_stack.addWidget(QTextEdit("Platzhalter..."))
        tabs = QTabWidget()
        w_routes = QWidget()
        l_r = QVBoxLayout(w_routes)
        self.route_list_widget = QListWidget()
        self.route_list_widget.itemClicked.connect(self.show_route_details)
        btn_del_route = QPushButton("Route löschen")
        btn_del_route.clicked.connect(self.delete_selected_route)
        l_r.addWidget(self.route_list_widget)
        l_r.addWidget(btn_del_route)
        tabs.addTab(w_routes, "Routen")
        w_objs = QWidget()
        l_o = QVBoxLayout(w_objs)
        self.object_list_widget = QListWidget()
        self.object_list_widget.itemClicked.connect(
            self.on_object_list_clicked
        )
        btn_edit_obj = QPushButton("Position bearbeiten")
        btn_edit_obj.clicked.connect(self.edit_selected_object)
        btn_del_obj = QPushButton("Objekt entfernen")
        btn_del_obj.clicked.connect(self.delete_selected_object_from_list)
        l_o.addWidget(self.object_list_widget)
        l_o.addWidget(btn_edit_obj)
        l_o.addWidget(btn_del_obj)
        tabs.addTab(w_objs, "Objekte")
        self.bottom_right_stack.addWidget(tabs)
        return gb

    def edit_selected_object(self):
        selected = self.sim_scene.selectedItems()
        if not selected:
            return
        item = selected[0]
        cx, cy, name = 0, 0, "Unbekannt"
        if isinstance(item, ShelfItem):
            cx = item.rect().x() + SHELF_SIZE / 2
            cy = item.rect().y() + SHELF_SIZE / 2
            name = "Regal"
        elif isinstance(item, CheckoutItem):
            cx = item.pos().x()
            cy = item.pos().y()
            name = f"Kasse #{item.data_id}"

        was_sim_maximized = self.is_sim_maximized
        if not was_sim_maximized:
            self.toggle_simulation_fullscreen(force=True)

        dlg = ObjectPositionDialog(name, cx, cy, self)

        def on_pos_change(nx, ny):
            if isinstance(item, ShelfItem):
                try:
                    best_i, min_d = -1, 9999
                    for i, pos in enumerate(self.all_shelves):
                        dist = (pos - QPointF(cx, cy)).manhattanLength()
                        if dist < min_d:
                            min_d = dist
                            best_i = i
                    if best_i != -1:
                        self.all_shelves[best_i] = QPointF(nx, ny)
                        self.save_data_generic(
                            self.shelves_file,
                            [[p.x(), p.y()] for p in self.all_shelves],
                        )
                        self.draw_debug_elements()
                except:
                    pass
            elif isinstance(item, CheckoutItem):
                for c in self.checkouts_data:
                    if c["id"] == item.data_id:
                        c["x"] = nx
                        c["y"] = ny
                        self.save_data_generic(
                            self.checkouts_file, self.checkouts_data
                        )
                        self.draw_debug_elements()
                        break

        dlg.position_changed.connect(on_pos_change)
        dlg.exec()
        if not was_sim_maximized:
            self.toggle_simulation_fullscreen(force=True)
        self.update_object_list()

    def simulation_tick(self):
        ac, wc = [], 0
        for c in self.customers:
            c.tick()
            if c.state == "FINISHED_SHOPPING":
                wc += 1
                if c.assigned_checkout_id is None:
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
                        self.checkout_queues[chosen_id].append(c)
                        c_data = next(
                            (
                                x
                                for x in self.checkouts_data
                                if x["id"] == chosen_id
                            ),
                            None,
                        )
                        if c_data:
                            cx, cy = c_data["x"], c_data["y"]
                            ori = c_data.get("orientation", "Right")
                            c_type = c_data["type"]
                            offset_key = "offset_queue_right"
                            if c_type == "SB":
                                offset_key = "offset_queue_sb_" + (
                                    "left" if ori == "Left" else "right"
                                )
                            else:
                                offset_key = "offset_queue_" + (
                                    "left" if ori == "Left" else "right"
                                )
                            off = self.settings[offset_key]
                            sx = cx + off[0]
                            sy = cy + off[1]
                            q_idx = len(self.checkout_queues[chosen_id]) - 1
                            target = QPointF(sx, sy + (q_idx * QUEUE_SPACING))
                            c.go_to_queue(target, chosen_id)
            if c.state == "IN_QUEUE" and c.assigned_checkout_id is not None:
                q = self.checkout_queues.get(c.assigned_checkout_id, [])
                if q and q[0] == c:
                    dist = (
                        QVector2D(c.pos()) - QVector2D(c.target_pos)
                    ).length()
                    if dist < 5.0:
                        c.state = "SCANNING"
            if c.state == "LEAVING" and c.assigned_checkout_id is not None:
                cid = c.assigned_checkout_id
                if (
                    cid in self.checkout_queues
                    and self.checkout_queues[cid]
                    and self.checkout_queues[cid][0] == c
                ):
                    self.checkout_queues[cid].pop(0)
                    self.advance_queue(cid)
                    c.assigned_checkout_id = None
            if c.state == "GONE":
                self.sim_scene.removeItem(c)
            else:
                ac.append(c)
        self.customers = ac
        self.lbl_queue_count.setText(str(wc))

    def advance_queue(self, cid):
        if cid not in self.checkout_queues:
            return
        c_data = next((x for x in self.checkouts_data if x["id"] == cid), None)
        if not c_data:
            return
        cx, cy = c_data["x"], c_data["y"]
        ori = c_data.get("orientation", "Right")
        c_type = c_data["type"]
        offset_key = "offset_queue_right"
        if c_type == "SB":
            offset_key = "offset_queue_sb_" + (
                "left" if ori == "Left" else "right"
            )
        else:
            offset_key = "offset_queue_" + (
                "left" if ori == "Left" else "right"
            )
        off = self.settings[offset_key]
        sx = cx + off[0]
        sy = cy + off[1]
        for idx, customer in enumerate(self.checkout_queues[cid]):
            target = QPointF(sx, sy + (idx * QUEUE_SPACING))
            customer.target_pos = target
            if customer.state != "SCANNING":
                customer.state = "IN_QUEUE"

    def open_settings_dialog(self):
        was_sim_maximized = self.is_sim_maximized
        if not was_sim_maximized:
            self.toggle_simulation_fullscreen(force=True)
        self.highlight_queues = True
        self.draw_debug_elements()
        dlg = SettingsDialog(self.settings, self)
        dlg.settings_changed.connect(self.apply_live_settings)
        dlg.exec()
        self.save_settings()
        self.highlight_queues = False
        self.draw_debug_elements()
        if not was_sim_maximized:
            self.toggle_simulation_fullscreen(force=True)

    def update_object_list(self):
        self.object_list_widget.clear()
        for c in self.checkouts_data:
            item = QListWidgetItem(f"Kasse #{c.get('id')} ({c.get('type')})")
            item.setData(
                Qt.ItemDataRole.UserRole,
                {"type": "checkout", "id": c.get("id")},
            )
            self.object_list_widget.addItem(item)
        for i, pos in enumerate(self.all_shelves):
            item = QListWidgetItem(
                f"Regal #{i+1} ({int(pos.x())}, {int(pos.y())})"
            )
            item.setData(
                Qt.ItemDataRole.UserRole, {"type": "shelf", "index": i}
            )
            self.object_list_widget.addItem(item)

    def on_object_list_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        self.sim_scene.clearSelection()
        target_item = None
        if data["type"] == "checkout":
            for ci in self.checkout_items:
                if ci.data_id == data["id"]:
                    target_item = ci
                    break
        elif data["type"] == "shelf":
            if data["index"] < len(self.shelf_items):
                target_item = self.shelf_items[data["index"]]
        if target_item:
            target_item.setSelected(True)

    def on_scene_selection_changed(self):
        selected = self.sim_scene.selectedItems()
        if not selected:
            return
        sel_item = selected[0]
        for i in range(self.object_list_widget.count()):
            l_item = self.object_list_widget.item(i)
            data = l_item.data(Qt.ItemDataRole.UserRole)
            match = False
            if (
                isinstance(sel_item, CheckoutItem)
                and data["type"] == "checkout"
                and data["id"] == sel_item.data_id
            ):
                match = True
            elif (
                isinstance(sel_item, ShelfItem)
                and data["type"] == "shelf"
                and self.shelf_items.index(sel_item) == data["index"]
            ):
                match = True
            if match:
                self.object_list_widget.setCurrentItem(l_item)
                break

    def delete_selected_object_from_list(self):
        selected_items = self.sim_scene.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        if isinstance(item, ShelfItem):
            try:
                idx = self.shelf_items.index(item)
                del self.all_shelves[idx]
                self.save_data_generic(
                    self.shelves_file,
                    [[p.x(), p.y()] for p in self.all_shelves],
                )
            except:
                pass
        elif isinstance(item, CheckoutItem):
            self.delete_checkout_by_id(item.data_id)
        self.draw_debug_elements()
        self.update_object_list()

    def update_checkout_table(self):
        self.checkout_table.setRowCount(len(self.checkouts_data))
        for i, c_data in enumerate(self.checkouts_data):
            self.checkout_table.setItem(
                i, 0, QTableWidgetItem(str(c_data.get("id", i + 1)))
            )
            ori = c_data.get("orientation", "R")
            typ_str = f"{c_data['type']} ({ori})"
            self.checkout_table.setItem(i, 1, QTableWidgetItem(typ_str))
            chk_open = QCheckBox()
            chk_open.setChecked(c_data["open"])
            chk_open.toggled.connect(
                lambda checked, idx=i: self.on_checkout_status_changed(
                    idx, checked
                )
            )
            w_status = QWidget()
            l = QHBoxLayout(w_status)
            l.addWidget(chk_open)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)
            self.checkout_table.setCellWidget(i, 2, w_status)
            if c_data["type"] == "Normal":
                combo = QComboBox()
                combo.addItems(["Azubi", "Erfahren", "Profi"])
                combo.setCurrentText(c_data.get("skill", "Azubi"))
                combo.currentTextChanged.connect(
                    lambda text, idx=i: self.on_checkout_skill_changed(
                        idx, text
                    )
                )
                self.checkout_table.setCellWidget(i, 3, combo)
            else:
                self.checkout_table.setItem(i, 3, QTableWidgetItem("-"))
            spin_max = QSpinBox()
            spin_max.setRange(1, 50)
            spin_max.setValue(c_data.get("max_queue", 5))
            spin_max.valueChanged.connect(
                lambda val, idx=i: self.on_checkout_max_queue_changed(idx, val)
            )
            self.checkout_table.setCellWidget(i, 4, spin_max)

    def delete_checkout_by_id(self, c_id):
        for i, c_data in enumerate(self.checkouts_data):
            if c_data["id"] == c_id:
                del self.checkouts_data[i]
                self.save_data_generic(
                    self.checkouts_file, self.checkouts_data
                )
                self.draw_debug_elements()
                self.update_checkout_table()
                return

    def load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r") as f:
                    self.settings.update(json.load(f))
            except:
                pass

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def apply_live_settings(self, ns):
        self.settings = ns
        self.draw_debug_elements()

    def save_data_generic(self, fp, d):
        with open(fp, "w") as f:
            json.dump(d, f)

    def load_data(self):
        if self.routes_file.exists():
            try:
                with open(self.routes_file, "r") as f:
                    data = json.load(f)
                    self.all_routes = {
                        k: [QPointF(p[0], p[1]) for p in v]
                        for k, v in data.items()
                    }
                for n in self.all_routes:
                    self.route_list_widget.addItem(n)
            except:
                pass
        if self.shelves_file.exists():
            try:
                with open(self.shelves_file, "r") as f:
                    data = json.load(f)
                    self.all_shelves = [QPointF(p[0], p[1]) for p in data]
            except:
                pass
        if self.waiting_area_file.exists():
            try:
                with open(self.waiting_area_file, "r") as f:
                    self.waiting_area_rect = QRectF(*json.load(f))
                    self.draw_waiting_area()
            except:
                pass
        if self.checkouts_file.exists():
            try:
                with open(self.checkouts_file, "r") as f:
                    self.checkouts_data = json.load(f)
            except:
                pass
        self.update_checkout_table()
        self.draw_debug_elements()
        self.update_object_list()

    def draw_waiting_area(self):
        if self.waiting_area_item:
            self.sim_scene.removeItem(self.waiting_area_item)
        if self.waiting_area_rect and self.settings.get(
            "show_waiting_area", True
        ):
            self.waiting_area_item = WaitingAreaItem(self.waiting_area_rect)
            self.sim_scene.addItem(self.waiting_area_item)

    def draw_debug_elements(self):
        self.draw_waiting_area()
        for i in self.shelf_items:
            self.sim_scene.removeItem(i)
        self.shelf_items.clear()
        show_s = self.settings["show_shelves"] or self.is_placing_shelves
        if show_s:
            for pos in self.all_shelves:
                s = ShelfItem(pos.x(), pos.y())
                s.setVisible(True)
                self.sim_scene.addItem(s)
                self.shelf_items.append(s)

        for i in self.checkout_items:
            self.sim_scene.removeItem(i)
        for i in self.route_debug_items:
            self.sim_scene.removeItem(i)
        for i in self.cashier_items:
            self.sim_scene.removeItem(i)
        self.checkout_items.clear()
        self.route_debug_items.clear()
        self.cashier_items.clear()

        if self.settings["show_checkouts"]:
            for cd in self.checkouts_data:
                if cd["type"] == "SB":
                    lo = (
                        self.settings["offset_light_sb_left"]
                        if cd.get("orientation", "Right") == "Left"
                        else self.settings["offset_light_sb_right"]
                    )
                else:
                    lo = (
                        self.settings["offset_light_normal_left"]
                        if cd.get("orientation", "Right") == "Left"
                        else self.settings["offset_light_normal_right"]
                    )

                it = CheckoutItem(
                    cd["x"],
                    cd["y"],
                    cd["type"],
                    cd.get("orientation", "Right"),
                    cd["open"],
                    self.settings["show_cashiers"]
                    and self.settings["show_checkouts"],
                    cd.get("id"),
                    lo,
                )
                self.sim_scene.addItem(it)
                self.checkout_items.append(it)
                ori = cd.get("orientation", "Right")
                c_type = cd["type"]
                offset_key = "offset_queue_right"
                if c_type == "SB":
                    offset_key = "offset_queue_sb_" + (
                        "left" if ori == "Left" else "right"
                    )
                else:
                    offset_key = "offset_queue_" + (
                        "left" if ori == "Left" else "right"
                    )
                off = self.settings[offset_key]
                start_x = cd["x"] + off[0]
                start_y = cd["y"] + off[1]
                end_x = start_x
                end_y = start_y + 60

                should_draw_queue = (
                    self.settings["show_routes"] or self.highlight_queues
                )
                if should_draw_queue:
                    line_pen = (
                        QPen(COLOR_QUEUE_HIGHLIGHT, 3, Qt.PenStyle.SolidLine)
                        if self.highlight_queues
                        else QPen(
                            QColor(200, 0, 0, 100), 2, Qt.PenStyle.DashLine
                        )
                    )
                    pp = QPainterPath()
                    pp.moveTo(start_x, start_y)
                    pp.lineTo(end_x, end_y)
                    line = QGraphicsPathItem(pp)
                    line.setPen(line_pen)
                    self.sim_scene.addItem(line)
                    self.route_debug_items.append(line)

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
                    cx = cd["x"] + off_c[0]
                    cy = cd["y"] + off_c[1]
                    cashier = CashierItem(cx, cy, cd.get("skill", "Azubi"))
                    self.sim_scene.addItem(cashier)
                    self.cashier_items.append(cashier)

        if self.settings["show_routes"]:
            route_pen = QPen(
                QColor(100, 100, 100, 100), 2, Qt.PenStyle.DotLine
            )
            for name, points in self.all_routes.items():
                if len(points) > 1:
                    path = QPainterPath()
                    path.moveTo(points[0])
                    [path.lineTo(p) for p in points[1:]]
                    pi = QGraphicsPathItem(path)
                    pi.setPen(route_pen)
                    pi.setZValue(4)
                    self.sim_scene.addItem(pi)
                    self.route_debug_items.append(pi)
        self.update_object_list()

    def finish_admin_action(self):
        if self.is_drawing_mode and self.current_route_points:
            name = f"Route_{len(self.all_routes) + 1}"
            self.all_routes[name] = list(self.current_route_points)
            data = {
                k: [[p.x(), p.y()] for p in v]
                for k, v in self.all_routes.items()
            }
            self.save_data_generic(self.routes_file, data)
            self.route_list_widget.addItem(name)
        elif self.is_placing_shelves:
            self.save_data_generic(
                self.shelves_file, [[p.x(), p.y()] for p in self.all_shelves]
            )
        elif self.is_drawing_waiting_area and self.waiting_area_rect:
            data = [
                self.waiting_area_rect.x(),
                self.waiting_area_rect.y(),
                self.waiting_area_rect.width(),
                self.waiting_area_rect.height(),
            ]
            self.save_data_generic(self.waiting_area_file, data)
        self.cancel_admin_action()

    def cancel_admin_action(self):
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_placing_checkout = False
        if self.current_route_path_item:
            self.sim_scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for i in self.current_route_point_items:
            self.sim_scene.removeItem(i)
        self.current_route_point_items.clear()
        self.admin_toolbar.hide()
        self.top_row_widget.show()
        self.bottom_right_group_box.show()
        self.bottom_left_group_box.setTitle("Routen-Editor")
        self.bottom_left_group_box.setEnabled(False)
        self.draw_debug_elements()

    def toggle_admin_mode(self, checked):
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
            if self.item_q1:
                self.item_q1.setEnabled(False)
            self.update_object_list()
        else:
            self.cancel_admin_action()
            self.top_left_stack.setCurrentIndex(0)
            self.bottom_right_stack.setCurrentIndex(0)
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            self.bottom_left_group_box.setEnabled(True)
            if self.item_q1:
                self.item_q1.setEnabled(True)

    def start_checkout_mode(self, c_type, orientation):
        self.is_placing_checkout = True
        self.current_checkout_type = c_type
        self.current_checkout_orientation = orientation
        self.setup_admin_fullscreen(f"Kasse ({c_type} - {orientation})")

    def start_shelf_mode(self):
        self.is_placing_shelves = True
        self.setup_admin_fullscreen("Regale platzieren")
        self.draw_debug_elements()

    def start_waiting_area_mode(self):
        self.is_drawing_waiting_area = True
        self.setup_admin_fullscreen("Wartebereich ziehen")
        if self.waiting_area_item:
            self.waiting_area_item.setVisible(True)

    def start_drawing_mode(self):
        self.is_drawing_mode = True
        self.setup_admin_fullscreen("Route zeichnen")
        self.current_route_points = []
        pen = QPen(COLOR_ORANGE, 3, Qt.PenStyle.DashLine)
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(pen)
        self.sim_scene.addItem(self.current_route_path_item)

    def setup_admin_fullscreen(self, title):
        self.top_row_widget.hide()
        self.bottom_right_group_box.hide()
        self.admin_toolbar.show()
        self.bottom_left_group_box.setTitle(f"Editor: {title}")
        self.bottom_left_group_box.setEnabled(True)

    def handle_scene_click(self, pos):
        if self.is_drawing_mode:
            self.current_route_points.append(pos)
            dot = self.sim_scene.addEllipse(
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
                p = QPainterPath()
                p.moveTo(self.current_route_points[0])
                [p.lineTo(x) for x in self.current_route_points[1:]]
                self.current_route_path_item.setPath(p)
        elif self.is_placing_shelves:
            self.all_shelves.append(pos)
            shelf = ShelfItem(pos.x(), pos.y())
            shelf.setVisible(True)
            self.sim_scene.addItem(shelf)
            self.shelf_items.append(shelf)
            self.update_object_list()
        elif self.is_placing_checkout:
            new_id = len(self.checkouts_data) + 1
            self.checkouts_data.append(
                {
                    "id": new_id,
                    "x": pos.x(),
                    "y": pos.y(),
                    "type": self.current_checkout_type,
                    "orientation": self.current_checkout_orientation,
                    "open": True,
                    "skill": (
                        "Azubi"
                        if self.current_checkout_type == "Normal"
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
        self.waiting_area_rect = rect
        self.draw_waiting_area()

    def toggle_simulation(self):
        if self.sim_timer.isActive():
            self.stop_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.all_routes:
            return
        count = self.actor_count_input.value()
        route_names = list(self.all_routes.keys())
        self.clear_customers()
        self.queue_count = 0
        self.draw_debug_elements()
        self.checkout_queues = {}
        for _ in range(count):
            r_name = random.choice(route_names)
            customer = CustomerItem(
                self.all_routes[r_name],
                self.all_shelves,
                self.waiting_area_rect,
            )
            self.sim_scene.addItem(customer)
            self.customers.append(customer)
        self.start_sim_button.setText("Stop")
        self.sim_timer.start(SIM_TICK_MS)

    def stop_simulation(self):
        self.sim_timer.stop()
        self.start_sim_button.setText("Start")

    def clear_customers(self):
        [self.sim_scene.removeItem(c) for c in self.customers]
        self.customers.clear()
        self.checkout_queues = {}

    def delete_selected_route(self):
        sel = self.route_list_widget.selectedItems()
        if not sel:
            return
        name = sel[0].text()
        del self.all_routes[name]
        self.route_list_widget.takeItem(self.route_list_widget.row(sel[0]))
        data = {
            k: [[p.x(), p.y()] for p in v] for k, v in self.all_routes.items()
        }
        self.save_data_generic(self.routes_file, data)
        self.draw_debug_elements()

    def on_checkout_status_changed(self, idx, is_open):
        self.checkouts_data[idx]["open"] = is_open
        self.save_data_generic(self.checkouts_file, self.checkouts_data)
        self.draw_debug_elements()

    def on_checkout_skill_changed(self, idx, skill):
        self.checkouts_data[idx]["skill"] = skill
        self.save_data_generic(self.checkouts_file, self.checkouts_data)

    def on_checkout_max_queue_changed(self, idx, val):
        self.checkouts_data[idx]["max_queue"] = val
        self.save_data_generic(self.checkouts_file, self.checkouts_data)

    def show_route_details(self, item):
        pass

    def toggle_simulation_fullscreen(self, force=False):
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
        if not self.item_q1 or self.is_admin_mode:
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
