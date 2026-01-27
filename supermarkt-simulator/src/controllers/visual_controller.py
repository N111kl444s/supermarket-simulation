"""
Visual Controller.
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
)
from views.items import (
    CheckoutItem,
    ShelfItem,
    CashierItem,
    CustomerItem,
    WaitingAreaItem,
    StartAreaItem,
    ExitAreaItem,
)


class VisualController:
    def __init__(self, scene, settings, translator=None):
        self.scene = scene
        self.settings = settings
        self.translator = translator

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
        self.screen_items = []

        self.waiting_area_item = None
        self.start_area_item = None
        self.exit_area_item = None
        self.background_item = None

        self.on_checkout_clicked = None
        self.on_shelf_clicked = None
        
        # Store checkout data for translation refresh
        self.checkout_data = []

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

        # AREAS
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

        show_c_nums = self.settings.get("show_checkout_numbers", True)
        show_queues = (
            self.settings.get("show_queues", False) or highlight_queues
        )
        
        # Store checkout data for translation refresh
        self.checkout_data = map_manager.checkouts_data.copy() if map_manager.checkouts_data else []
        
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
        # ... (Identischer Code wie zuvor) ...
        # Damit der Code kompakt bleibt, hier nur Referenz.
        # Der bestehende Code von _draw_single_checkout und _draw_queue_visuals wird hier wiederverwendet.
        # Da ich dir die Datei komplett geben soll, kopiere ich den Inhalt der vorherigen Version hier hinein.

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

        if c_type == "Normal" and self.settings["show_cashiers"] and (is_open or is_malfunction):
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
            cai.setData(0, cd["id"])  # Store checkout id
            cai.setParentItem(self.map_group)
            cai.setZValue(25)
            self.cashier_items.append(cai)

            # Set repair icon if malfunction
            cai.set_repairing(cd.get("malfunction", False))

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

            # Create screen with background rect
            screen_item = QGraphicsRectItem(-sw / 2, -sh / 2, sw, sh)
            screen_item.setData(0, cd.get("id"))
            screen_item.setBrush(QBrush(COLOR_SCREEN_OPEN if is_open else COLOR_SCREEN_CLOSED))
            screen_item.setPen(QPen(Qt.PenStyle.NoPen))

            # Create text item (will be updated in update_checkout_status)
            if is_open:
                status_text = self.translator.get("stats.checkout_open") if self.translator else "Geöffnet"
            else:
                status_text = self.translator.get("stats.checkout_closed") if self.translator else "Geschlossen"
            
            text_item = QGraphicsSimpleTextItem(status_text, parent=screen_item)
            text_item.setBrush(QBrush(COLOR_SCREEN_TEXT))
            font = QFont("Segoe UI", 10, QFont.Weight.Bold)
            text_item.setFont(font)
            text_item.setData(1, "text")  # Mark as text item
            text_item.setZValue(1)  # Text should be above background

            brect = text_item.boundingRect()
            if brect.width() > 0 and brect.height() > 0:
                target_w = sw * 0.9
                target_h = sh * 0.9
                scale = min(target_w / brect.width(), target_h / brect.height())
                text_item.setScale(scale)
                tx_scaled = brect.width() * scale
                ty_scaled = brect.height() * scale
                text_item.setPos(-tx_scaled / 2, -ty_scaled / 2)

            # Create icon item (for tool.png during malfunction, initially hidden)
            icon_item = QGraphicsPixmapItem(parent=screen_item)
            icon_item.setData(1, "icon")  # Mark as icon item
            icon_item.setVisible(False)
            icon_item.setZValue(10)  # Icon must be above text and background
            
            # Create angry icon item (for angry.png during conflict, initially hidden)
            angry_icon_item = QGraphicsPixmapItem(parent=screen_item)
            angry_icon_item.setData(1, "angry_icon")  # Mark as angry icon item
            angry_icon_item.setVisible(False)
            angry_icon_item.setZValue(10)  # Icon must be above text and background

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

    def sync_customers(self, models):
        # Sync Customers
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

    def sync_all_agents(self, customers, workers):
        self.sync_customers(customers)
        # Workers removed, no sync needed

    def update_checkout_status(self, checkouts_data):
        data_map = {cd["id"]: cd for cd in checkouts_data}

        for screen_item in self.screen_items:
            cid = screen_item.data(0)
            if cid is None or cid not in data_map:
                continue
            
            cd = data_map[cid]
            is_malfunction = cd.get("malfunction", False)
            is_open = cd.get("open", True)
            
            # Get child items
            text_item = None
            icon_item = None
            angry_icon_item = None
            
            for child in screen_item.childItems():
                child_type = child.data(1)
                if child_type == "text" and isinstance(child, QGraphicsSimpleTextItem):
                    text_item = child
                elif child_type == "icon" and isinstance(child, QGraphicsPixmapItem):
                    icon_item = child
                elif child_type == "angry_icon" and isinstance(child, QGraphicsPixmapItem):
                    angry_icon_item = child
            
            # Check for conflict (angry customer)
            is_conflict = cd.get("conflict", False)
            
            if is_malfunction:
                print(f"DEBUG: Malfunction detected at checkout {cid}")
                # Show tool icon (no blinking, just static)
                if icon_item:
                    if not icon_item.pixmap() or icon_item.pixmap().isNull():
                        # Load tool.png
                        from config import ICON_DIR
                        tool_path = ICON_DIR / "tool.png"
                        print(f"DEBUG: Loading tool icon from {tool_path}, exists: {tool_path.exists()}")
                        if tool_path.exists():
                            tool_pixmap = QPixmap(str(tool_path))
                            print(f"DEBUG: Pixmap loaded, isNull: {tool_pixmap.isNull()}, size: {tool_pixmap.width()}x{tool_pixmap.height()}")
                            if not tool_pixmap.isNull():
                                # Get screen size from settings (in scene units)
                                c_type = cd.get("type", "Normal")
                                if c_type == "SB":
                                    sw = float(self.settings.get("size_screen_sb_width", 10.0))
                                    sh = float(self.settings.get("size_screen_sb_height", 10.0))
                                else:
                                    sw = float(self.settings.get("size_screen_normal_width", 15.0))
                                    sh = float(self.settings.get("size_screen_normal_height", 10.0))
                                
                                # Use original pixmap and scale via setScale() for better quality
                                # Icon should be 50% of the smaller screen dimension
                                icon_item.setPixmap(tool_pixmap)
                                
                                # Calculate scale factor: desired size / original size
                                desired_size_in_scene = min(sw, sh)
                                original_size = tool_pixmap.width()  # 512px
                                scale_factor = desired_size_in_scene / original_size
                                
                                icon_item.setScale(scale_factor)
                                icon_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                                
                                print(f"DEBUG: Screen size: {sw}x{sh} scene units, desired icon size: {desired_size_in_scene}, scale factor: {scale_factor}")
                                
                                # Get screen rect to center icon properly
                                screen_rect = screen_item.boundingRect()
                                icon_rect = icon_item.boundingRect()
                                
                                # Center icon in screen coordinates (before scaling is applied)
                                icon_item.setPos(
                                    screen_rect.center().x() - (icon_rect.width() * scale_factor) / 2,
                                    screen_rect.center().y() - (icon_rect.height() * scale_factor) / 2
                                )
                                icon_item.setZValue(10)  # Ensure icon is on top
                                print(f"DEBUG: Icon original size: {tool_pixmap.width()}x{tool_pixmap.height()} pixels, scaled by {scale_factor}, positioned at {icon_item.pos()}, z-value: {icon_item.zValue()}")
                    else:
                        print(f"DEBUG: Icon already loaded, size: {icon_item.pixmap().width()}x{icon_item.pixmap().height()}")
                    
                    # Show icon (no blinking)
                    icon_item.setVisible(True)
                    print(f"DEBUG: Icon visible: {icon_item.isVisible()}, opacity: {icon_item.opacity()}")
                else:
                    print(f"DEBUG: No icon_item found for checkout {cid}")
                
                # Hide text and angry icon during malfunction
                if text_item:
                    text_item.setVisible(False)
                if angry_icon_item:
                    angry_icon_item.setVisible(False)
                
                # White background during repair
                screen_item.setBrush(QBrush(QColor(0, 0, 0)))  # Black
                
            elif is_conflict:
                print(f"DEBUG: Conflict detected at checkout {cid}")
                # Show angry icon
                if angry_icon_item:
                    if not angry_icon_item.pixmap() or angry_icon_item.pixmap().isNull():
                        # Load angry.png
                        from config import ICON_DIR
                        angry_path = ICON_DIR / "angry.png"
                        print(f"DEBUG: Loading angry icon from {angry_path}, exists: {angry_path.exists()}")
                        if angry_path.exists():
                            angry_pixmap = QPixmap(str(angry_path))
                            print(f"DEBUG: Angry pixmap loaded, isNull: {angry_pixmap.isNull()}, size: {angry_pixmap.width()}x{angry_pixmap.height()}")
                            if not angry_pixmap.isNull():
                                # Get screen size from settings (in scene units)
                                c_type = cd.get("type", "Normal")
                                if c_type == "SB":
                                    sw = float(self.settings.get("size_screen_sb_width", 10.0))
                                    sh = float(self.settings.get("size_screen_sb_height", 10.0))
                                else:
                                    sw = float(self.settings.get("size_screen_normal_width", 15.0))
                                    sh = float(self.settings.get("size_screen_normal_height", 10.0))
                                
                                # Use original pixmap and scale via setScale() for better quality
                                # Icon should be 50% of the smaller screen dimension
                                angry_icon_item.setPixmap(angry_pixmap)
                                
                                # Calculate scale factor: desired size / original size
                                desired_size_in_scene = min(sw, sh)
                                original_size = angry_pixmap.width()
                                scale_factor = desired_size_in_scene / original_size
                                
                                angry_icon_item.setScale(scale_factor)
                                angry_icon_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                                
                                print(f"DEBUG: Angry icon - Screen size: {sw}x{sh}, desired size: {desired_size_in_scene}, scale: {scale_factor}")
                                
                                # Get screen rect to center icon properly
                                screen_rect = screen_item.boundingRect()
                                icon_rect = angry_icon_item.boundingRect()
                                
                                # Center icon in screen coordinates (before scaling is applied)
                                angry_icon_item.setPos(
                                    screen_rect.center().x() - (icon_rect.width() * scale_factor) / 2,
                                    screen_rect.center().y() - (icon_rect.height() * scale_factor) / 2
                                )
                                angry_icon_item.setZValue(10)
                                print(f"DEBUG: Angry icon positioned at {angry_icon_item.pos()}, z-value: {angry_icon_item.zValue()}")
                    
                    # Show angry icon
                    angry_icon_item.setVisible(True)
                    print(f"DEBUG: Angry icon visible: {angry_icon_item.isVisible()}")
                else:
                    print(f"DEBUG: No angry_icon_item found for checkout {cid}")
                
                # Hide text and tool icon during conflict
                if text_item:
                    text_item.setVisible(False)
                if icon_item:
                    icon_item.setVisible(False)
                
                # Orange/red background during conflict
                screen_item.setBrush(QBrush(QColor(255, 150, 0)))  # Orange
                
            else:
                # No malfunction or conflict - show normal status
                if icon_item:
                    icon_item.setVisible(False)
                if angry_icon_item:
                    angry_icon_item.setVisible(False)
                
                # Show and update text
                if text_item:
                    status_text = self.translator.get("stats.checkout_open") if is_open else self.translator.get("stats.checkout_closed")
                    if not self.translator:
                        status_text = "Geöffnet" if is_open else "Geschlossen"
                    text_item.setText(status_text)
                    text_item.setBrush(QBrush(COLOR_SCREEN_TEXT))
                    text_item.setVisible(True)
                
                # Update background color
                col = COLOR_SCREEN_OPEN if is_open else COLOR_SCREEN_CLOSED
                screen_item.setBrush(QBrush(col))

        # Remove cashier repair status updates (moved to screen)
        # No longer updating cashier items for repair visualization

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

        # Customers & Workers clearen wir hier nicht explizit, das macht sync

        self.shelf_items.clear()
        self.checkout_items.clear()
        self.cashier_items.clear()
        self.route_debug_items.clear()
        self.queue_debug_items.clear()
        self.screen_items.clear()
    def refresh_checkout_displays(self, translator):
        """Refresh all checkout display text with new translations."""
        self.translator = translator
        
        # Update text in all screen items by removing old ones and recreating
        # Remove old screen items
        for screen_item in self.screen_items:
            screen_item.setParentItem(None)
        self.screen_items.clear()
        
        # Recreate screen items with new translations for all stored checkout data
        for cd in self.checkout_data:
            self._redraw_checkout_screen(cd)
    
    def _redraw_checkout_screen(self, cd):
        """Redraw a single checkout screen with current translation."""
        c_type = cd.get("type", "Normal")
        is_sb = c_type == "SB"
        ori = cd.get("orientation", "Right")
        angle = cd.get("angle", 0)
        is_open = cd.get("open", True)
        is_malfunction = cd.get("malfunction", False)
        
        # Calculate screen_offset using the SAME logic as _draw_single_checkout
        suffix = "left" if ori == "Left" else "right"
        key_offset = (
            "offset_screen_sb_" + suffix
            if is_sb
            else "offset_screen_normal_" + suffix
        )
        screen_offset = self.settings.get(key_offset, [0, 0])
        
        # Get screen size based on checkout type (SB or Normal) - MUST MATCH _draw_single_checkout
        if is_sb:
            sw = float(self.settings.get("size_screen_sb_width", 10.0))
            sh = float(self.settings.get("size_screen_sb_height", 10.0))
        else:
            sw = float(self.settings.get("size_screen_normal_width", 15.0))
            sh = float(self.settings.get("size_screen_normal_height", 10.0))
        
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
        
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
            status_text = self.translator.get("stats.disruption") if self.translator else "STÖRUNG"
            text_col = QColor("red")
        else:
            if is_open:
                status_text = self.translator.get("stats.checkout_open") if self.translator else "Geöffnet"
            else:
                status_text = self.translator.get("stats.checkout_closed") if self.translator else "Geschlossen"
            text_col = COLOR_SCREEN_TEXT

        text_item = QGraphicsSimpleTextItem(status_text, parent=screen_item)
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