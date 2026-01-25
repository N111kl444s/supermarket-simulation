"""
Visual Controller.
Refactored:
- FIX: Worker items are now correctly synchronized and added to the scene.
- FIX: Added visualization for 'worker_routes' (Orange).
"""

import math
import time
from PyQt6.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
    QGraphicsSimpleTextItem,
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from config import (
    COLOR_BLUE,
    COLOR_RED,
    CASHIER_SIZE,
    IMAGE_DIR,
    COLOR_SCREEN_OPEN,
    COLOR_SCREEN_CLOSED,
    COLOR_SCREEN_TEXT,
    COLOR_WORKER_SPAWN,
)
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
    StartAreaItem,
    ExitAreaItem,
    WorkerItem,
)


class VisualController:
    def __init__(self, scene, settings):
        self.scene = scene
        self.settings = settings

        self.earth_item = None
        self.map_group = QGraphicsRectItem()
        self.map_group.setPen(QPen(Qt.PenStyle.NoPen))
        self.map_group.setBrush(QBrush(Qt.BrushStyle.NoBrush))

        self.shelf_items = []
        self.checkout_items = []
        self.cashier_items = []
        self.route_debug_items = []
        self.queue_debug_items = []
        self.customer_items = {}
        self.worker_items = {}
        self.screen_items = []

        self.waiting_area_item = None
        self.start_area_item = None
        self.exit_area_item = None
        self.worker_area_item = None
        self.background_item = None

        self.on_checkout_clicked = None
        self.on_shelf_clicked = None

        self._init_earth()

    def _init_earth(self):
        earth_path = IMAGE_DIR / "earth.png"
        if earth_path.exists():
            pix = QPixmap(str(earth_path))
            self.earth_item = QGraphicsPixmapItem(pix)
            self.earth_item.setZValue(-1000)
            self.earth_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.scene.addItem(self.earth_item)
            self.scene.setSceneRect(0, 0, pix.width(), pix.height())
        else:
            self.scene.setSceneRect(0, 0, 5000, 5000)

        self.scene.addItem(self.map_group)
        self.map_group.setZValue(0)

    def get_map_center(self):
        if (
            self.background_item
            and self.background_item.parentItem() == self.map_group
        ):
            return self.background_item.sceneBoundingRect().center()
        rect = self.map_group.childrenBoundingRect()
        if not rect.isEmpty():
            return self.map_group.mapToScene(rect.center())
        pos = self.map_group.pos()
        return pos + QPointF(100, 100)

    def set_checkout_click_callback(self, callback):
        self.on_checkout_clicked = callback

    def set_shelf_click_callback(self, callback):
        self.on_shelf_clicked = callback

    def update_background(self, image_path, scale, maps_dir):
        if self.background_item:
            self.background_item.setParentItem(None)
            if self.background_item.scene():
                self.scene.removeItem(self.background_item)
        self.background_item = None
        if image_path:
            bg_path = maps_dir / image_path
            if bg_path.exists():
                pix = QPixmap(str(bg_path))
                self.background_item = QGraphicsPixmapItem(pix)
                self.background_item.setZValue(-100)
                self.background_item.setScale(scale)
                self.background_item.setAcceptedMouseButtons(
                    Qt.MouseButton.NoButton
                )
                self.background_item.setParentItem(self.map_group)

    def update_bg_scale(self, scale):
        if self.background_item:
            self.background_item.setScale(scale)

    def draw_map_elements(
        self, map_manager, selected_spec=None, highlight_queues=False
    ):
        self.scene.blockSignals(True)
        self._clear_dynamic_items()

        self.map_group.setPos(map_manager.map_pos_x, map_manager.map_pos_y)
        if (
            self.background_item
            and self.background_item.parentItem() != self.map_group
        ):
            self.background_item.setParentItem(self.map_group)

        def is_selected(obj_type, idx_or_id):
            if not selected_spec:
                return False
            if selected_spec["type"] != obj_type:
                return False
            if obj_type == "shelf":
                return selected_spec["index"] == idx_or_id
            if obj_type == "checkout":
                return selected_spec["id"] == idx_or_id
            return False

        if map_manager.waiting_area_rect and self.settings.get(
            "show_waiting_area", True
        ):
            self.waiting_area_item = WaitingAreaItem(
                map_manager.waiting_area_rect
            )
            self.waiting_area_item.setParentItem(self.map_group)
            self.waiting_area_item.setZValue(1)
        if map_manager.start_area_rect and self.settings.get(
            "show_start_area", True
        ):
            self.start_area_item = StartAreaItem(map_manager.start_area_rect)
            self.start_area_item.setParentItem(self.map_group)
            self.start_area_item.setZValue(1)
        if map_manager.exit_area_rect and self.settings.get(
            "show_exit_area", True
        ):
            self.exit_area_item = ExitAreaItem(map_manager.exit_area_rect)
            self.exit_area_item.setParentItem(self.map_group)
            self.exit_area_item.setZValue(1)

        if map_manager.worker_spawn_rect and self.settings.get(
            "show_worker_area", True
        ):
            w_item = QGraphicsRectItem(map_manager.worker_spawn_rect)
            w_item.setBrush(QBrush(COLOR_WORKER_SPAWN))
            w_item.setPen(QPen(Qt.PenStyle.DashLine))
            w_item.setParentItem(self.map_group)
            w_item.setZValue(1)

            t = QGraphicsSimpleTextItem("Techniker", w_item)
            t.setBrush(QBrush(Qt.GlobalColor.black))
            t.setPos(map_manager.worker_spawn_rect.topLeft() + QPointF(5, 5))

            self.worker_area_item = w_item

        show_s_nums = self.settings.get("show_shelf_numbers", True)
        for idx, s_data in enumerate(map_manager.all_shelves):
            sx = s_data.get("x", 0)
            sy = s_data.get("y", 0)
            show = self.settings["show_shelves"] or is_selected("shelf", idx)
            if show:
                s = ShelfItem(
                    sx,
                    sy,
                    index=idx,
                    size=self.settings.get("size_shelf", 32),
                    show_label=show_s_nums,
                    angle=s_data.get("angle", 0),
                    variant=s_data.get("variant", 0),
                    mirrored=s_data.get("mirrored", False),
                )
                if self.on_shelf_clicked:
                    s.clicked.connect(self.on_shelf_clicked)
                s.setParentItem(self.map_group)
                self.shelf_items.append(s)
                if is_selected("shelf", idx):
                    s.setSelected(True)

        show_c_nums = self.settings.get("show_checkout_numbers", True)
        show_queues = (
            self.settings.get("show_queues", False) or highlight_queues
        )
        for cd in map_manager.checkouts_data:
            show = self.settings["show_checkouts"] or is_selected(
                "checkout", cd["id"]
            )
            if show:
                self._draw_single_checkout(
                    cd, is_selected("checkout", cd["id"]), show_id=show_c_nums
                )
            if show_queues:
                self._draw_queue_visuals(cd)

        if self.settings["show_routes"]:
            self._draw_routes(map_manager)
        self.scene.blockSignals(False)

    def _draw_single_checkout(self, cd, is_selected, show_id=True):
        ori = cd.get("orientation", "Right")
        angle = cd.get("angle", 0)
        c_type = cd["type"]
        is_sb = c_type == "SB"
        is_open = cd.get("open", True)
        is_malfunction = cd.get("malfunction", False)

        suffix = "left" if ori == "Left" else "right"
        key_offset = (
            "offset_screen_sb_" + suffix
            if is_sb
            else "offset_screen_normal_" + suffix
        )
        screen_offset = self.settings.get(key_offset, [0, 0])

        if is_sb:
            sw = float(self.settings.get("size_screen_sb_width", 10.0))
            sh = float(self.settings.get("size_screen_sb_height", 10.0))
        else:
            sw = float(self.settings.get("size_screen_normal_width", 15.0))
            sh = float(self.settings.get("size_screen_normal_height", 10.0))

        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)

        ci = CheckoutItem(
            cd["x"],
            cd["y"],
            c_type,
            ori,
            is_open,
            show_screen=False,
            data_id=cd.get("id"),
            screen_offset=screen_offset,
            width=cw,
            height=ch,
            angle=angle,
            show_id=show_id,
        )
        if self.on_checkout_clicked:
            ci.clicked.connect(self.on_checkout_clicked)
        ci.setParentItem(self.map_group)
        self.checkout_items.append(ci)
        if is_selected:
            ci.setSelected(True)

        if c_type == "Normal" and self.settings["show_cashiers"] and is_open:
            skill = cd.get("cashier_skill") or cd.get("skill") or "Azubi"
            checkout_id = cd.get("id", 1)
            variant = max(0, checkout_id - 1)
            offset_key = (
                "offset_cashier_left"
                if ori == "Left"
                else "offset_cashier_right"
            )
            off_x, off_y = self.settings.get(offset_key, [0, 0])
            cx, cy = cd["x"], cd["y"]
            center_x = cx + cw / 2
            center_y = cy + ch / 2
            p_unrot_x = cx + float(off_x)
            p_unrot_y = cy + float(off_y)
            rad = math.radians(angle)
            tx = p_unrot_x - center_x
            ty = p_unrot_y - center_y
            rx = tx * math.cos(rad) - ty * math.sin(rad)
            ry = tx * math.sin(rad) + ty * math.cos(rad)
            final_x = rx + center_x
            final_y = ry + center_y

            cai = CashierItem(
                final_x,
                final_y,
                skill,
                size=self.settings.get("size_cashier", CASHIER_SIZE),
                variant_index=variant,
            )
            cai.setParentItem(self.map_group)
            cai.setZValue(25)
            self.cashier_items.append(cai)

        if self.settings["show_cashiers"]:
            cx, cy = cd["x"], cd["y"]
            center_x = cx + cw / 2
            center_y = cy + ch / 2
            lox, loy = screen_offset
            if lox == 0 and loy == 0:
                lox, loy = cw / 2, 10
            lox = float(lox)
            loy = float(loy)
            p_unrot_x = cx + lox
            p_unrot_y = cy + loy
            rad = math.radians(angle)
            tx = p_unrot_x - center_x
            ty = p_unrot_y - center_y
            rx = tx * math.cos(rad) - ty * math.sin(rad)
            ry = tx * math.sin(rad) + ty * math.cos(rad)
            screen_x = rx + center_x
            screen_y = ry + center_y

            screen_item = QGraphicsRectItem(-sw / 2, -sh / 2, sw, sh)
            screen_item.setData(0, cd.get("id"))

            if is_malfunction:
                col = QColor("yellow")
            else:
                col = COLOR_SCREEN_OPEN if is_open else COLOR_SCREEN_CLOSED

            screen_item.setBrush(QBrush(col))
            screen_item.setPen(QPen(Qt.PenStyle.NoPen))

            if is_malfunction:
                status_text = "STÖRUNG"
                text_col = QColor("red")
            else:
                status_text = "Geöffnet" if is_open else "Geschlossen"
                text_col = COLOR_SCREEN_TEXT

            text_item = QGraphicsSimpleTextItem(
                status_text, parent=screen_item
            )
            text_item.setBrush(QBrush(text_col))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            text_item.setFont(font)

            brect = text_item.boundingRect()
            if brect.width() > 0 and brect.height() > 0:
                target_w = sw * 0.9
                target_h = sh * 0.9
                scale = min(
                    target_w / brect.width(), target_h / brect.height()
                )
                text_item.setScale(scale)
                tx_scaled = brect.width() * scale
                ty_scaled = brect.height() * scale
                text_item.setPos(-tx_scaled / 2, -ty_scaled / 2)

            screen_item.setPos(screen_x, screen_y)
            screen_item.setRotation(angle)
            screen_item.setZValue(15)
            screen_item.setParentItem(self.map_group)
            screen_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
            self.screen_items.append(screen_item)

    def _draw_queue_visuals(self, cd):
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
        spacing = self.settings.get("dist_queue_spacing", 20)
        dot_size = self.settings.get("size_queue_dot", 4)
        max_q = cd.get("max_queue", 5)
        cx, cy = cd["x"], cd["y"]
        angle = cd.get("angle", 0)

        offset_key = (
            "offset_queue_"
            + ("sb_" if cd["type"] == "SB" else "")
            + ("left" if cd["orientation"] == "Left" else "right")
        )
        off = self.settings.get(offset_key, [0, 0])
        center_x = cx + cw / 2
        center_y = cy + ch / 2
        p_unrot_x = cx + float(off[0])
        p_unrot_y = cy + float(off[1])
        rad = math.radians(angle)
        tx = p_unrot_x - center_x
        ty = p_unrot_y - center_y
        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)
        start_point_x = rx + center_x
        start_point_y = ry + center_y

        if cd.get("orientation") == "Left":
            dir_rad = math.radians(angle)
        else:
            dir_rad = math.radians(angle + 180)

        dir_x = math.cos(dir_rad)
        dir_y = math.sin(dir_rad)

        for i in range(max_q):
            px = start_point_x + dir_x * (i * spacing)
            py = start_point_y + dir_y * (i * spacing)
            current_size = dot_size
            if i == 0:
                current_size = dot_size + 4
                dot = QGraphicsEllipseItem(
                    px - current_size / 2,
                    py - current_size / 2,
                    current_size,
                    current_size,
                )
                dot.setBrush(QBrush(Qt.GlobalColor.red))
            else:
                dot = QGraphicsEllipseItem(
                    px - current_size / 2,
                    py - current_size / 2,
                    current_size,
                    current_size,
                )
                dot.setBrush(QBrush(QColor(255, 165, 0, 180)))
            dot.setPen(QPen(Qt.GlobalColor.white, 1))
            dot.setZValue(20)
            dot.setParentItem(self.map_group)
            self.queue_debug_items.append(dot)

    def _draw_routes(self, map_manager):
        def draw(routes, col):
            for pts in routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pen = QPen(col, 2, Qt.PenStyle.DotLine)
                    pen.setCosmetic(True)
                    pi.setPen(pen)
                    pi.setZValue(4)
                    pi.setParentItem(self.map_group)
                    self.route_debug_items.append(pi)

        draw(map_manager.shop_routes, QColor(100, 100, 100, 100))
        draw(map_manager.start_routes, COLOR_BLUE)
        draw(map_manager.exit_routes, COLOR_RED)
        draw(map_manager.worker_routes, QColor("orange"))  # NEU

    def sync_customers(self, models):
        current_set = set(models)
        to_remove = []
        for model, item in self.customer_items.items():
            if model not in current_set:
                item.setParentItem(None)
                if item.scene():
                    self.scene.removeItem(item)
                to_remove.append(model)
        for m in to_remove:
            del self.customer_items[m]

        for model in models:
            if model not in self.customer_items:
                item = CustomerItem(
                    model, size=self.settings.get("size_customer", 32)
                )
                item.setParentItem(self.map_group)
                self.customer_items[model] = item
            else:
                self.customer_items[model].sync_visuals()

    def _sync_workers(self, worker_models):
        current_set = set(worker_models)
        to_remove = []
        for model, item in self.worker_items.items():
            if model not in current_set:
                item.setParentItem(None)
                if item.scene():
                    self.scene.removeItem(item)
                to_remove.append(model)
        for m in to_remove:
            del self.worker_items[m]

        for model in worker_models:
            if model not in self.worker_items:
                try:
                    item = WorkerItem(
                        model, size=self.settings.get("size_customer", 32)
                    )
                    item.setParentItem(self.map_group)
                    item.sync_visuals()
                    self.worker_items[model] = item
                    print(
                        f"DEBUG: WorkerItem NEU erstellt bei {model.pos.x()}, {model.pos.y()}"
                    )
                except Exception as e:
                    print(f"ERROR beim Erstellen des WorkerItem: {e}")
            else:
                self.worker_items[model].sync_visuals()

    def sync_all_agents(self, customers, workers):
        self.sync_customers(customers)
        self._sync_workers(workers)

    def update_checkout_status(self, checkouts_data):
        blink_state = int(time.time() * 2) % 2 == 0
        data_map = {cd["id"]: cd for cd in checkouts_data}

        for item in self.screen_items:
            cid = item.data(0)
            if cid is not None and cid in data_map:
                cd = data_map[cid]
                is_malfunction = cd.get("malfunction", False)
                is_open = cd.get("open", True)

                text_item = None
                for child in item.childItems():
                    if isinstance(child, QGraphicsSimpleTextItem):
                        text_item = child
                        break

                if is_malfunction:
                    col = QColor("yellow") if blink_state else QColor("red")
                    item.setBrush(QBrush(col))
                    if text_item:
                        text_item.setText("STÖRUNG")
                        text_col = (
                            QColor("black") if blink_state else QColor("white")
                        )
                        text_item.setBrush(QBrush(text_col))
                else:
                    col = COLOR_SCREEN_OPEN if is_open else COLOR_SCREEN_CLOSED
                    item.setBrush(QBrush(col))
                    if text_item:
                        text_item.setText(
                            "Geöffnet" if is_open else "Geschlossen"
                        )
                        text_item.setBrush(QBrush(COLOR_SCREEN_TEXT))

    def _clear_dynamic_items(self):
        for i in (
            self.shelf_items
            + self.checkout_items
            + self.cashier_items
            + self.route_debug_items
            + self.queue_debug_items
            + self.screen_items
        ):
            i.setParentItem(None)
            if i.scene():
                self.scene.removeItem(i)

        if self.waiting_area_item:
            self.waiting_area_item.setParentItem(None)
        if self.start_area_item:
            self.start_area_item.setParentItem(None)
        if self.exit_area_item:
            self.exit_area_item.setParentItem(None)
        if self.worker_area_item:
            self.worker_area_item.setParentItem(None)

        for item in self.customer_items.values():
            item.setParentItem(None)
            if item.scene():
                self.scene.removeItem(item)
        self.customer_items.clear()

        for item in self.worker_items.values():
            item.setParentItem(None)
            if item.scene():
                self.scene.removeItem(item)
        self.worker_items.clear()

        self.shelf_items.clear()
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()
        self.queue_debug_items.clear()
        self.screen_items.clear()
