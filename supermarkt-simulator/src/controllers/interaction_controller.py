"""
Interaction Controller.
Handles user inputs, tools (Shelf, Route, Checkout tools), and editing logic.
Updated: Handles click on Shelves/Checkouts to open Editor Wizard.
"""

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsView, QInputDialog
from PyQt6.QtGui import QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QObject, pyqtSignal
from config import COLOR_ORANGE, COLOR_BLUE, COLOR_RED, COLOR_DARK_TEXT
from views.dialogs import ObjectPositionDialog, CheckoutConfigDialog

class InteractionController(QObject): 
    
    map_data_changed = pyqtSignal()

    def __init__(self, scene, map_manager, visual_controller, view, sim_manager):
        super().__init__()
        self.scene = scene
        self.map_manager = map_manager
        self.visual_controller = visual_controller
        self.view = view 
        self.sim_manager = sim_manager
        
        self.active_tool = None
        self.active_tool_params = {}
        
        self.current_route_points = []
        self.current_route_path_item = None
        self.current_route_point_items = []
        
        self.current_angle = 0
        self.current_mirrored = False
        
        self.scene.clicked_point.connect(self.handle_scene_click)
        self.scene.waiting_area_created.connect(self.handle_area_created)
        
        # Callbacks verbinden
        self.visual_controller.set_checkout_click_callback(self.handle_checkout_click)
        self.visual_controller.set_shelf_click_callback(self.handle_shelf_click)

    def set_tool(self, tool_name, params=None, button_ref=None):
        self._reset_ui_buttons(exclude_btn=button_ref)
        if tool_name is None:
            self._reset_internal_state()
            return

        if button_ref and button_ref.isChecked():
            self.active_tool = tool_name
            self.active_tool_params = params or {}
            
            self.current_angle = 0
            self.current_mirrored = False
            
            if "route" in tool_name:
                self.view.is_drawing_mode = (tool_name == "route")
                self.view.is_drawing_start_route = (tool_name == "start_route")
                self.view.is_drawing_exit_route = (tool_name == "exit_route")
                self.view.admin_toolbar.show()
                color = COLOR_ORANGE if tool_name == "route" else (COLOR_BLUE if tool_name == "start_route" else COLOR_RED)
                self._init_temp_path(color)
            elif "area" in tool_name:
                self.view.is_drawing_waiting_area = (tool_name == "waiting_area")
                self.view.is_drawing_start_area = (tool_name == "start_area")
                self.view.is_drawing_exit_area = (tool_name == "exit_area")
            elif tool_name == "shelf":
                self.view.is_placing_shelves = True
            elif tool_name == "checkout":
                self.view.is_placing_checkout = True
                
            if self.view.sim_view: 
                self.view.sim_view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.visual_controller.draw_map_elements(self.map_manager)
        else:
            self.set_tool(None)

    def handle_key_press(self, event):
        if not self.active_tool: return
        key = event.key()
        
        if key == Qt.Key.Key_R:
            self.current_angle = (self.current_angle + 90) % 360
            print(f"Rotation: {self.current_angle}°")
        elif key == Qt.Key.Key_F:
            self.current_mirrored = not self.current_mirrored
            print(f"Mirrored: {self.current_mirrored}")

    def _reset_internal_state(self):
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
        self.current_route_points = []
        
        if self.view.sim_view: 
            self.view.sim_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.visual_controller.draw_map_elements(self.map_manager)

    def _reset_ui_buttons(self, exclude_btn):
        btns = [
            self.view.new_route_button, self.view.place_shelves_button,
            self.view.waiting_area_button, self.view.start_area_button,
            self.view.btn_start_route, self.view.btn_exit_route, self.view.btn_exit_area,
            self.view.btn_kl, self.view.btn_kr, self.view.btn_sl, self.view.btn_sr
        ]
        for b in btns:
            if b != exclude_btn: b.setChecked(False)

    def _init_temp_path(self, color):
        self.current_route_points = []
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(QPen(color, 3, Qt.PenStyle.DashLine))
        self.scene.addItem(self.current_route_path_item)

    def handle_scene_click(self, pos):
        if not self.view.is_admin_mode: return

        if self.active_tool in ["route", "start_route", "exit_route"]:
            self.current_route_points.append(pos)
            dot = self.scene.addEllipse(pos.x()-4, pos.y()-4, 8, 8, QPen(COLOR_DARK_TEXT), QBrush(COLOR_ORANGE))
            dot.setZValue(10)
            self.current_route_point_items.append(dot)
            if len(self.current_route_points) > 1:
                pp = QPainterPath()
                pp.moveTo(self.current_route_points[0])
                [pp.lineTo(x) for x in self.current_route_points[1:]]
                self.current_route_path_item.setPath(pp)
                
        elif self.active_tool == "shelf":
            variant, ok = QInputDialog.getInt(self.view, "Regal Variante", "Wähle Design (1-5):", 1, 1, 5, 1)
            if ok:
                self.map_manager.all_shelves.append({
                    "x": pos.x(),
                    "y": pos.y(),
                    "angle": self.current_angle,
                    "variant": variant,
                    "mirrored": self.current_mirrored
                })
                self.visual_controller.draw_map_elements(self.map_manager)
                self.map_data_changed.emit() 
            
        elif self.active_tool == "checkout":
            new_id = (max([c["id"] for c in self.map_manager.checkouts_data], default=0) + 1)
            
            self.map_manager.checkouts_data.append({
                "id": new_id, 
                "x": pos.x(), 
                "y": pos.y(),
                "type": self.active_tool_params.get("type"),
                "orientation": self.active_tool_params.get("ori"),
                "open": True, 
                "skill": "Azubi", 
                "max_queue": 5, 
                "angle": self.current_angle 
            })
            self.visual_controller.draw_map_elements(self.map_manager)
            self.map_data_changed.emit()

    def handle_area_created(self, rect):
        if self.active_tool == "waiting_area": self.map_manager.waiting_area_rect = rect
        elif self.active_tool == "start_area": self.map_manager.start_area_rect = rect
        elif self.active_tool == "exit_area": self.map_manager.exit_area_rect = rect
        self.visual_controller.draw_map_elements(self.map_manager)

    def finish_route_drawing(self):
        if self.current_route_points:
            if self.active_tool == "route":
                name = f"ShopRoute_{len(self.map_manager.shop_routes)+1}"
                self.map_manager.shop_routes[name] = list(self.current_route_points)
            elif self.active_tool == "start_route":
                name = f"StartRoute_{len(self.map_manager.start_routes)+1}"
                self.map_manager.start_routes[name] = list(self.current_route_points)
            elif self.active_tool == "exit_route":
                name = f"ExitRoute_{len(self.map_manager.exit_routes)+1}"
                self.map_manager.exit_routes[name] = list(self.current_route_points)
            
            self.map_data_changed.emit()
            
        self.set_tool(None)
        self.visual_controller.draw_map_elements(self.map_manager)

    def cancel_route_drawing(self):
        self.set_tool(None)
        self.visual_controller.draw_map_elements(self.map_manager)
        
    def edit_object_position(self, obj_spec):
        if not obj_spec: return
        cx, cy, name, cur_ori, cur_ang, cur_var = 0, 0, "Objekt", None, 0, 1
        obj_type = obj_spec["type"]
        
        if obj_type == "shelf":
            idx = obj_spec["index"]
            if idx < len(self.map_manager.all_shelves):
                data = self.map_manager.all_shelves[idx]
                cx, cy = data["x"], data["y"]
                cur_ang = data.get("angle", 0)
                cur_var = data.get("variant", 1)
                name = f"Regal #{idx+1}"
        elif obj_type == "checkout":
            cid = obj_spec["id"]
            c = next((x for x in self.map_manager.checkouts_data if x["id"] == cid), None)
            if c:
                cx, cy, name = c["x"], c["y"], f"Kasse #{cid}"
                cur_ori, cur_ang = c.get("orientation", "Right"), c.get("angle", 0)
        
        dlg = ObjectPositionDialog(
            name, cx, cy, 
            orientation=cur_ori, 
            angle=cur_ang, 
            variant=cur_var if obj_type=="shelf" else None,
            parent=self.view
        )
        
        def update_pos(nx, ny):
            if obj_type == "shelf": 
                self.map_manager.all_shelves[obj_spec["index"]]["x"] = nx
                self.map_manager.all_shelves[obj_spec["index"]]["y"] = ny
            elif obj_type == "checkout": 
                c = next((x for x in self.map_manager.checkouts_data if x["id"] == obj_spec["id"]), None)
                if c: c["x"], c["y"] = nx, ny
            self.visual_controller.draw_map_elements(self.map_manager, selected_spec=obj_spec)
            
        def update_ori(no):
            c = next((x for x in self.map_manager.checkouts_data if x["id"] == obj_spec["id"]), None)
            if c: c["orientation"] = no
            self.visual_controller.draw_map_elements(self.map_manager, selected_spec=obj_spec)
            
        def update_ang(na):
            if obj_type == "shelf":
                self.map_manager.all_shelves[obj_spec["index"]]["angle"] = na
            elif obj_type == "checkout":
                c = next((x for x in self.map_manager.checkouts_data if x["id"] == obj_spec["id"]), None)
                if c: c["angle"] = na
            self.visual_controller.draw_map_elements(self.map_manager, selected_spec=obj_spec)

        def update_var(nv):
            if obj_type == "shelf":
                self.map_manager.all_shelves[obj_spec["index"]]["variant"] = nv
            self.visual_controller.draw_map_elements(self.map_manager, selected_spec=obj_spec)

        dlg.position_changed.connect(update_pos)
        if cur_ori: dlg.orientation_changed.connect(update_ori)
        dlg.angle_changed.connect(update_ang)
        if obj_type == "shelf": dlg.variant_changed.connect(update_var)
        
        dlg.exec()
        self.visual_controller.draw_map_elements(self.map_manager, selected_spec=obj_spec)

    def handle_checkout_click(self, checkout_id):
        """Unified handler for checkout clicks."""
        current_mode = self.view.mode_combo.currentText()
        
        if current_mode == "Editor":
            # Editor -> Position Wizard
            self.edit_object_position({"type": "checkout", "id": checkout_id})
            
        elif current_mode == "Simulation":
            # Simulation -> Config Dialog (if not running)
            if self.sim_manager.is_running: return 
            
            c_data = next((x for x in self.map_manager.checkouts_data if x["id"] == checkout_id), None)
            if not c_data: return
            dlg = CheckoutConfigDialog(c_data, self.view)
            if dlg.exec():
                c_data.update(dlg.get_data())
                self.visual_controller.draw_map_elements(self.map_manager)

    def handle_shelf_click(self, index):
        """Unified handler for shelf clicks."""
        current_mode = self.view.mode_combo.currentText()
        
        if current_mode == "Editor":
            # Editor -> Position Wizard
            self.edit_object_position({"type": "shelf", "index": index})
            
        elif current_mode == "Simulation":
            # Simulation -> (Optional: Info anzeigen?) Aktuell nichts.
            pass

    def delete_object(self, obj_spec):
        if not obj_spec: return
        if obj_spec["type"] == "shelf":
            idx = obj_spec["index"]
            if idx < len(self.map_manager.all_shelves): 
                del self.map_manager.all_shelves[idx]
        elif obj_spec["type"] == "checkout":
            self.map_manager.checkouts_data = [c for c in self.map_manager.checkouts_data if c["id"] != obj_spec["id"]]
        
        self.visual_controller.draw_map_elements(self.map_manager)
        self.map_data_changed.emit()