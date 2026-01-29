"""
Interaction Controller.
"""

from PyQt6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsEllipseItem,
    QInputDialog,
    QGraphicsView,
)
from PyQt6.QtGui import QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QPointF, QObject, pyqtSignal, QRectF
from config import COLOR_ORANGE, COLOR_BLUE, COLOR_RED, COLOR_DARK_TEXT
from views.dialogs import ObjectPositionDialog, CheckoutConfigDialog


class InteractionController(QObject):

    map_data_changed = pyqtSignal()

    def __init__(
        self, scene, map_manager, visual_controller, view, sim_manager
    ):
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

        self.visual_controller.set_checkout_click_callback(
            self.handle_checkout_click
        )
        self.visual_controller.set_shelf_click_callback(
            self.handle_shelf_click
        )

    def set_tool(self, tool_name, params=None, button_ref=None):
        if button_ref:
            self._reset_ui_buttons(exclude_btn=button_ref)

        # If switching away from route drawing, hide admin toolbar
        if self.active_tool and "route" in self.active_tool and (
            not tool_name or "route" not in tool_name
        ):
            self.view.is_drawing_mode = False
            self.view.admin_toolbar.hide()
            self._clear_temp_drawing()

        if tool_name is None:
            self._reset_internal_state()
            return

        if button_ref and button_ref.isChecked():
            self.active_tool = tool_name
            self.active_tool_params = params or {}

            self.current_angle = 0
            self.current_mirrored = False

            self._clear_temp_drawing()

            if "route" in tool_name:
                self.view.is_drawing_mode = True
                color = (
                    COLOR_ORANGE
                    if tool_name == "route"
                    else (
                        COLOR_BLUE if tool_name == "start_route" else COLOR_RED
                    )
                )
                self.view.admin_toolbar.show()
                self._init_temp_path(color)
            elif "area" in tool_name:
                self.view.is_drawing_waiting_area = tool_name == "waiting_area"
                self.view.is_drawing_start_area = tool_name == "start_area"
                self.view.is_drawing_exit_area = tool_name == "exit_area"
                self.view.is_drawing_worker_area = (
                    tool_name == "worker_area"
                )  # NEU
            elif tool_name == "shelf":
                self.view.is_placing_shelves = True
            elif tool_name == "checkout":
                self.view.is_placing_checkout = True
            elif tool_name == "move_map":
                pass

            self.visual_controller.draw_map_elements(self.map_manager)
        else:
            self.set_tool(None)

    def handle_key_press(self, event):
        if not self.active_tool:
            return
        key = event.key()
        if key == Qt.Key.Key_R:
            self.current_angle = (self.current_angle + 90) % 360
        elif key == Qt.Key.Key_F:
            self.current_mirrored = not self.current_mirrored

    def _reset_internal_state(self):
        self.active_tool = None
        self.view.is_drawing_mode = False
        self.view.is_placing_shelves = False
        self.view.is_drawing_waiting_area = False
        self.view.is_drawing_start_area = False
        self.view.is_drawing_exit_area = False
        self.view.is_drawing_worker_area = False  # NEU
        self.view.is_placing_checkout = False
        self.view.admin_toolbar.hide()
        self._clear_temp_drawing()
        self.visual_controller.draw_map_elements(self.map_manager)

    def _clear_temp_drawing(self):
        if self.current_route_path_item:
            self.current_route_path_item.setParentItem(None)
            if self.current_route_path_item.scene():
                self.scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for i in self.current_route_point_items:
            i.setParentItem(None)
            if i.scene():
                self.scene.removeItem(i)
        self.current_route_point_items.clear()
        self.current_route_points = []

    def _reset_ui_buttons(self, exclude_btn=None):
        btns = [
            self.view.new_route_button,
            self.view.place_shelves_button,
            self.view.waiting_area_button,
            self.view.start_area_button,
            self.view.btn_start_route,
            self.view.btn_exit_route,
            self.view.btn_exit_area,
            self.view.btn_checkout_normal,
            self.view.btn_checkout_sb,
            self.view.btn_move_map,
        ]
        for b in btns:
            if b != exclude_btn:
                b.setChecked(False)

    def _init_temp_path(self, color):
        from PyQt6.QtWidgets import QGraphicsPathItem

        self.current_route_points = []
        self.current_route_path_item = QGraphicsPathItem()
        pen = QPen(color, 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True)
        self.current_route_path_item.setPen(pen)
        self.current_route_path_item.setParentItem(
            self.visual_controller.map_group
        )

    def handle_scene_click(self, global_pos):
        if not self.view.is_admin_mode:
            return

        if not self.active_tool:
            return

        local_pos = self.visual_controller.map_group.mapFromScene(global_pos)

        if self.active_tool == "move_map":
            self.map_manager.map_pos_x = global_pos.x()
            self.map_manager.map_pos_y = global_pos.y()
            self.visual_controller.draw_map_elements(self.map_manager)
            return

        if self.active_tool in ["route", "start_route", "exit_route"]:
            self.current_route_points.append(local_pos)
            dot = QGraphicsEllipseItem(
                local_pos.x() - 4, local_pos.y() - 4, 8, 8
            )
            dot.setPen(QPen(COLOR_DARK_TEXT, 1))
            dot.setBrush(QBrush(COLOR_ORANGE))
            dot.setParentItem(self.visual_controller.map_group)
            self.current_route_point_items.append(dot)
            if len(self.current_route_points) > 1:
                pp = QPainterPath()
                pp.moveTo(self.current_route_points[0])
                [pp.lineTo(x) for x in self.current_route_points[1:]]
                self.current_route_path_item.setPath(pp)

        elif self.active_tool == "shelf":
            variant, ok = QInputDialog.getInt(
                self.view, "Regal Variante", "Wähle Design (1-5):", 1, 1, 5, 1
            )
            if ok:
                new_shelf = {
                    "x": local_pos.x(),
                    "y": local_pos.y(),
                    "angle": self.current_angle,
                    "variant": variant,
                    "mirrored": self.current_mirrored,
                }
                self.map_manager.all_shelves.append(new_shelf)
                self.map_data_changed.emit()

                new_idx = len(self.map_manager.all_shelves) - 1

                self.set_tool(None)
                self._reset_ui_buttons(None)

                spec = {"type": "shelf", "index": new_idx}
                self.visual_controller.draw_map_elements(
                    self.map_manager, selected_spec=spec
                )
                self.edit_object_position(spec)

        elif self.active_tool == "checkout":
            new_id = (
                max(
                    [c["id"] for c in self.map_manager.checkouts_data],
                    default=0,
                )
                + 1
            )
            new_checkout = {
                "id": new_id,
                "x": local_pos.x(),
                "y": local_pos.y(),
                "type": self.active_tool_params.get("type"),
                "orientation": self.active_tool_params.get("ori") or "Right",
                "open": True,
                "skill": "Azubi",
                "max_queue": 5,
                "angle": self.current_angle,
            }
            self.map_manager.checkouts_data.append(new_checkout)
            self.map_data_changed.emit()

            self.set_tool(None)
            self._reset_ui_buttons(None)

            spec = {"type": "checkout", "id": new_id}
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=spec
            )
            self.edit_object_position(spec)

    def handle_area_created(self, rect):
        tl = self.visual_controller.map_group.mapFromScene(rect.topLeft())
        local_rect = QRectF(tl.x(), tl.y(), rect.width(), rect.height())

        if self.active_tool == "waiting_area":
            self.map_manager.waiting_area_rect = local_rect
        elif self.active_tool == "start_area":
            self.map_manager.start_area_rect = local_rect
        elif self.active_tool == "exit_area":
            self.map_manager.exit_area_rect = local_rect
        elif self.active_tool == "worker_area":  # NEU
            self.map_manager.worker_spawn_rect = local_rect

        self.visual_controller.draw_map_elements(self.map_manager)
        self.set_tool(None)
        self._reset_ui_buttons(None)

    def finish_route_drawing(self):
        if self.current_route_points:
            if self.active_tool == "route":
                self.map_manager.shop_routes[
                    f"ShopRoute_{len(self.map_manager.shop_routes)+1}"
                ] = list(self.current_route_points)
            elif self.active_tool == "start_route":
                self.map_manager.start_routes[
                    f"StartRoute_{len(self.map_manager.start_routes)+1}"
                ] = list(self.current_route_points)
            elif self.active_tool == "exit_route":
                self.map_manager.exit_routes[
                    f"ExitRoute_{len(self.map_manager.exit_routes)+1}"
                ] = list(self.current_route_points)
            self.map_data_changed.emit()
        self.set_tool(None)
        self._reset_ui_buttons(None)
        self.visual_controller.draw_map_elements(self.map_manager)

    def cancel_route_drawing(self):
        self.set_tool(None)
        self._reset_ui_buttons(None)
        self.visual_controller.draw_map_elements(self.map_manager)

    def edit_object_position(self, obj_spec):
        if not obj_spec:
            return
        cx, cy, name, cur_ang, cur_var = 0, 0, "Objekt", 0, 1
        obj_type = obj_spec["type"]

        if obj_type == "shelf":
            idx = obj_spec["index"]
            if idx >= len(self.map_manager.all_shelves):
                return
            data = self.map_manager.all_shelves[idx]
            cx, cy = data["x"], data["y"]
            cur_ang = data.get("angle", 0)
            cur_var = data.get("variant", 1)
            name = f"Regal #{idx+1}"
        elif obj_type == "checkout":
            cid = obj_spec["id"]
            c = next(
                (x for x in self.map_manager.checkouts_data if x["id"] == cid),
                None,
            )
            if not c:
                return
            cx, cy, name = c["x"], c["y"], f"Kasse #{cid}"
            cur_ang = c.get("angle", 0)

        dlg = ObjectPositionDialog(
            name,
            cx,
            cy,
            angle=cur_ang,
            variant=cur_var if obj_type == "shelf" else None,
            parent=self.view,
            translator=self.view.translator if hasattr(self.view, "translator") else None,
        )

        def update_pos(nx, ny):
            if obj_type == "shelf":
                self.map_manager.all_shelves[obj_spec["index"]]["x"] = nx
                self.map_manager.all_shelves[obj_spec["index"]]["y"] = ny
            elif obj_type == "checkout":
                c = next(
                    (
                        x
                        for x in self.map_manager.checkouts_data
                        if x["id"] == obj_spec["id"]
                    ),
                    None,
                )
                if c:
                    c["x"], c["y"] = nx, ny
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=obj_spec
            )

        def update_ang(na):
            if obj_type == "shelf":
                self.map_manager.all_shelves[obj_spec["index"]]["angle"] = na
            elif obj_type == "checkout":
                c = next(
                    (
                        x
                        for x in self.map_manager.checkouts_data
                        if x["id"] == obj_spec["id"]
                    ),
                    None,
                )
                if c:
                    c["angle"] = na
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=obj_spec
            )

        def update_var(nv):
            if obj_type != "shelf":
                return
            self.map_manager.all_shelves[obj_spec["index"]]["variant"] = nv
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=obj_spec
            )

        dlg.position_changed.connect(update_pos)
        dlg.angle_changed.connect(update_ang)
        if obj_type == "shelf":
            dlg.variant_changed.connect(update_var)

        dlg.exec()
        self.visual_controller.draw_map_elements(
            self.map_manager, selected_spec=obj_spec
        )

    def handle_checkout_click(self, checkout_id):
        if self.active_tool:
            return

        current_mode = self.view.mode_combo.currentText()
        if current_mode == "Editor":
            self.set_tool(None)
            self._reset_ui_buttons(None)
            spec = {"type": "checkout", "id": checkout_id}
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=spec
            )
            self.edit_object_position(spec)
        elif current_mode == "Simulation":
            if self.sim_manager.is_running or self.sim_manager.is_initialized:
                return
            c_data = next(
                (
                    x
                    for x in self.map_manager.checkouts_data
                    if x["id"] == checkout_id
                ),
                None,
            )
            if not c_data:
                return

            dlg = CheckoutConfigDialog(
                c_data,
                self.view,
                translator=self.view.translator if hasattr(self.view, "translator") else None,
            )
            if dlg.exec():
                updated_data = dlg.get_data()
                c_data.update(updated_data)

                # Ensure both 'skill' and 'cashier_skill' are synchronized
                # to avoid inconsistencies with old map data
                if "skill" in updated_data:
                    c_data["cashier_skill"] = updated_data["skill"]

                self.visual_controller.draw_map_elements(self.map_manager)

    def handle_shelf_click(self, index):
        if self.active_tool:
            return

        current_mode = self.view.mode_combo.currentText()
        if current_mode == "Editor":
            self.set_tool(None)
            self._reset_ui_buttons(None)
            spec = {"type": "shelf", "index": index}
            self.visual_controller.draw_map_elements(
                self.map_manager, selected_spec=spec
            )
            self.edit_object_position(spec)

    def delete_object(self, obj_spec):
        if not obj_spec:
            return
        if obj_spec["type"] == "shelf":
            idx = obj_spec["index"]
            if idx < len(self.map_manager.all_shelves):
                del self.map_manager.all_shelves[idx]
        elif obj_spec["type"] == "checkout":
            self.map_manager.checkouts_data = [
                c
                for c in self.map_manager.checkouts_data
                if c["id"] != obj_spec["id"]
            ]
        self.visual_controller.draw_map_elements(self.map_manager)
        self.map_data_changed.emit()
