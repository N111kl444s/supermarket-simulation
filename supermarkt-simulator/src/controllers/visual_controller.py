"""
Visual Controller.
Refactored:
- FIX: Passes checkout dimensions and cashier size from settings to CheckoutItem.
- This ensures checkouts are scaled correctly (e.g. 28x14) instead of using raw image size.
"""

import math
from PyQt6.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QGraphicsRectItem,
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from config import COLOR_BLUE, COLOR_RED, CASHIER_SIZE, IMAGE_DIR
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
    StartAreaItem,
    ExitAreaItem,
)
from views.items.worker_item import WorkerItem


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
        self.light_items = []

        self.route_debug_items = []
        self.queue_debug_items = []
        self.customer_items = {}
        self.worker_items = {}

        self.waiting_area_item = None
        self.start_area_item = None
        self.exit_area_item = None
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

        # Pos vom MapManager übernehmen (FIX für "Verschoben")
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

        show_queues = (
            self.settings.get("show_queues", False) or highlight_queues
        )
        for cd in map_manager.checkouts_data:
            show = self.settings["show_checkouts"] or is_selected(
                "checkout", cd["id"]
            )
            if show:
                self._draw_single_checkout(
                    cd, map_manager, is_selected("checkout", cd["id"])
                )
            if show_queues:
                self._draw_queue_visuals(cd)

        if self.settings["show_routes"]:
            self._draw_routes(map_manager)
        self.scene.blockSignals(False)

    def _draw_single_checkout(self, cd, map_manager, is_selected):
        # FIX: Größe aus Settings holen
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
        c_size = self.settings.get("size_cashier", 10)

        ci = CheckoutItem(
            cd, map_manager, width=cw, height=ch, cashier_size=c_size
        )

        if self.on_checkout_clicked:
            ci.set_callback(self.on_checkout_clicked)

        ci.setParentItem(self.map_group)
        self.checkout_items.append(ci)

        if is_selected:
            ci.setSelected(True)

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
        p_unrot_x = cx + off[0]
        p_unrot_y = cy + off[1]

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
            if not routes:
                return
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
        draw(map_manager.maintenance_routes, QColor("orange"))

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

    def sync_workers(self, models):
        current_set = set(models)
        to_remove = []
        for model, item in self.worker_items.items():
            if model not in current_set:
                item.setParentItem(None)
                if item.scene():
                    self.scene.removeItem(item)
                to_remove.append(model)
        for m in to_remove:
            del self.worker_items[m]

        for model in models:
            if model not in self.worker_items:
                item = WorkerItem(model, size=32)
                item.setParentItem(self.map_group)
                self.worker_items[model] = item
            else:
                self.worker_items[model].sync_visuals()

    def _clear_dynamic_items(self):
        for i in (
            self.shelf_items
            + self.checkout_items
            + self.cashier_items
            + self.route_debug_items
            + self.queue_debug_items
            + self.light_items
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
        self.shelf_items.clear()
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()
        self.queue_debug_items.clear()
        self.light_items.clear()
