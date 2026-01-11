"""
Visual Controller.
Manages the graphical representation of the simulation (Scene, Items).
Updated: Passes visibility flags for numbering to items.
"""

import math
from PyQt6.QtGui import QColor, QPen, QBrush, QPixmap, QPainterPath
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsPathItem
from PyQt6.QtCore import Qt, QPointF
from config import COLOR_BLUE, COLOR_RED, CASHIER_SIZE
from views.items import (
    CheckoutItem, ShelfItem, CashierItem, CustomerItem, 
    WaitingAreaItem, StartAreaItem, ExitAreaItem
)

class VisualController:
    """
    Verwaltet die QGraphicsScene und alle visuellen Items.
    """
    def __init__(self, scene, settings):
        self.scene = scene
        self.settings = settings
        
        self.shelf_items = []
        self.checkout_items = []
        self.cashier_items = []
        self.route_debug_items = []
        self.customer_items = {} 
        
        self.waiting_area_item = None
        self.start_area_item = None
        self.exit_area_item = None
        self.background_item = None
        
        self.on_checkout_clicked = None 

    def set_checkout_click_callback(self, callback):
        self.on_checkout_clicked = callback

    def update_background(self, image_path, scale, maps_dir):
        if self.background_item and self.background_item.scene():
            self.scene.removeItem(self.background_item)
        self.background_item = None
        
        if image_path:
            bg_path = maps_dir / image_path
            if bg_path.exists():
                pix = QPixmap(str(bg_path))
                self.background_item = QGraphicsPixmapItem(pix)
                self.background_item.setZValue(-100)
                self.background_item.setScale(scale)
                self.scene.addItem(self.background_item)

    def update_bg_scale(self, scale):
        if self.background_item:
            self.background_item.setScale(scale)

    def draw_map_elements(self, map_manager, selected_spec=None, highlight_queues=False):
        self.scene.blockSignals(True)
        self._clear_static_items()
        
        if self.background_item and not self.background_item.scene():
            self.scene.addItem(self.background_item)

        def is_selected(obj_type, idx_or_id):
            if not selected_spec: return False
            if selected_spec["type"] != obj_type: return False
            if obj_type == "shelf": return selected_spec["index"] == idx_or_id
            if obj_type == "checkout": return selected_spec["id"] == idx_or_id
            return False

        # Areas
        if map_manager.waiting_area_rect and self.settings.get("show_waiting_area", True):
            self.waiting_area_item = WaitingAreaItem(map_manager.waiting_area_rect)
            self.scene.addItem(self.waiting_area_item)
        
        if map_manager.start_area_rect and self.settings.get("show_start_area", True):
            self.start_area_item = StartAreaItem(map_manager.start_area_rect)
            self.scene.addItem(self.start_area_item)
            
        if map_manager.exit_area_rect and self.settings.get("show_exit_area", True):
            self.exit_area_item = ExitAreaItem(map_manager.exit_area_rect)
            self.scene.addItem(self.exit_area_item)

        # Regale
        show_s_nums = self.settings.get("show_shelf_numbers", True)
        for idx, p in enumerate(map_manager.all_shelves):
            show = self.settings["show_shelves"] or is_selected("shelf", idx)
            if show:
                # FIX: show_label übergeben
                s = ShelfItem(p.x(), p.y(), index=idx, size=self.settings.get("size_shelf", 32), show_label=show_s_nums)
                self.scene.addItem(s)
                self.shelf_items.append(s)
                if is_selected("shelf", idx): s.setSelected(True)

        # Kassen & Kassierer
        show_c_nums = self.settings.get("show_checkout_numbers", True)
        for cd in map_manager.checkouts_data:
            show = self.settings["show_checkouts"] or is_selected("checkout", cd["id"])
            if show:
                # FIX: show_id übergeben
                self._draw_single_checkout(cd, is_selected("checkout", cd["id"]), show_id=show_c_nums)

        # Routen
        if self.settings["show_routes"]:
            self._draw_routes(map_manager)

        self.scene.blockSignals(False)

    def _draw_single_checkout(self, cd, is_selected, show_id=True):
        ori = cd.get("orientation", "Right")
        angle = cd.get("angle", 0)
        c_type = cd["type"]
        
        key_light = "offset_light_sb_" + ("left" if ori == "Left" else "right") if c_type == "SB" else "offset_light_normal_" + ("left" if ori == "Left" else "right")
        lo = self.settings.get(key_light, [0,0])
        
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
        
        ci = CheckoutItem(
            cd["x"], cd["y"], c_type, ori, cd["open"], self.settings["show_cashiers"], 
            cd.get("id"), lo, 
            width=cw, height=ch, angle=angle,
            show_id=show_id # Hier anwenden
        )
        if self.on_checkout_clicked:
            ci.clicked.connect(self.on_checkout_clicked)
        self.scene.addItem(ci)
        self.checkout_items.append(ci)
        if is_selected: ci.setSelected(True)

        # Kassierer
        if c_type == "Normal" and self.settings["show_cashiers"] and cd.get("open", True):
             skill = cd.get("cashier_skill") or cd.get("skill") or "Azubi"
             
             offset_key = "offset_cashier_left" if ori == "Left" else "offset_cashier_right"
             off_x, off_y = self.settings.get(offset_key, [0, 0])
             
             cx, cy = cd["x"], cd["y"]
             center_x = cx + cw / 2
             center_y = cy + ch / 2
             
             p_unrot_x = cx + off_x
             p_unrot_y = cy + off_y
             
             rad = math.radians(angle)
             tx = p_unrot_x - center_x
             ty = p_unrot_y - center_y
             
             rx = tx * math.cos(rad) - ty * math.sin(rad)
             ry = tx * math.sin(rad) + ty * math.cos(rad)
             
             final_x = rx + center_x
             final_y = ry + center_y

             cai = CashierItem(
                 final_x, final_y, 
                 skill, 
                 size=self.settings.get("size_cashier", CASHIER_SIZE)
             )
             self.scene.addItem(cai)
             self.cashier_items.append(cai)

    def _draw_routes(self, map_manager):
        def draw(routes, col):
            for pts in routes.values():
                if len(pts) > 1:
                    pp = QPainterPath()
                    pp.moveTo(pts[0])
                    [pp.lineTo(p) for p in pts[1:]]
                    pi = QGraphicsPathItem(pp)
                    pi.setPen(QPen(col, 2, Qt.PenStyle.DotLine))
                    pi.setZValue(4)
                    self.scene.addItem(pi)
                    self.route_debug_items.append(pi)
        draw(map_manager.shop_routes, QColor(100,100,100,100))
        draw(map_manager.start_routes, COLOR_BLUE)
        draw(map_manager.exit_routes, COLOR_RED)

    def sync_customers(self, models):
        current_set = set(models)
        to_remove = []
        for model, item in self.customer_items.items():
            if model not in current_set:
                self.scene.removeItem(item)
                to_remove.append(model)
        for m in to_remove:
            del self.customer_items[m]
        for model in models:
            if model not in self.customer_items:
                item = CustomerItem(model, size=self.settings.get("size_customer", 32))
                self.scene.addItem(item)
                self.customer_items[model] = item
            else:
                self.customer_items[model].sync_visuals()

    def _clear_static_items(self):
        for i in self.shelf_items + self.checkout_items + self.cashier_items + self.route_debug_items:
            if i.scene(): self.scene.removeItem(i)
        self.shelf_items.clear()
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()
        if self.waiting_area_item and self.waiting_area_item.scene(): self.scene.removeItem(self.waiting_area_item)
        if self.start_area_item and self.start_area_item.scene(): self.scene.removeItem(self.start_area_item)
        if self.exit_area_item and self.exit_area_item.scene(): self.scene.removeItem(self.exit_area_item)