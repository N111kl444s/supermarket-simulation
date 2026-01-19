"""
Customer agent logic.
Refactored:
- Customers spawn with 0 items.
- Item count increases during shopping phase.
- FIX: Handles new Dictionary-based Shelf data structure.
- UPDATE: Calculates facing angle based on movement.
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import WALK_SPEED_PPS, WALK_SPEED_DISABLED_FACTOR, SCAN_TIME_PER_ITEM_MS

class CustomerModel:
    def __init__(
        self,
        shopping_route,
        shelves,
        start_area_rect,
        waiting_area_rect,
        exit_area_rect=None,
        start_routes=None,
        exit_routes=None,
        max_offset=10,
        is_disabled=False,
        # Uniform Params (Min, Max)
        scan_speed_range=(0.5, 1.5),
        # Normal Params (Mean, Std)
        speed_walk_params=(2.5, 0.5),
        speed_roll_params=(1.5, 0.3),
        items_params=(12, 4)
    ):
        self.shopping_route = shopping_route
        self.all_shelves = shelves 
        self.start_area = start_area_rect
        self.waiting_area = waiting_area_rect
        self.exit_area = exit_area_rect
        
        self.available_start_routes = start_routes if start_routes else {}
        self.available_exit_routes = exit_routes if exit_routes else {}

        self.max_offset = max_offset
        self.is_disabled = is_disabled

        self.pos = QPointF(0, 0)
        self.angle = 0.0 # NEU: Blickrichtung in Grad
        
        self.state = "SPAWNING"
        self.path = []
        self.target_pos = None
        
        # --- BEWEGUNG (Normalverteilung) ---
        if self.is_disabled:
            mu, sigma = speed_roll_params
        else:
            mu, sigma = speed_walk_params
            
        val = random.normalvariate(mu, sigma)
        self.speed = max(0.1, val)

        # --- ARTIKELANZAHL (Normalverteilung) ---
        mu_items, sigma_items = items_params
        item_val = int(random.normalvariate(mu_items, sigma_items))
        
        self.item_count = 0  
        self.target_item_count = max(1, item_val)
        
        self.target_shelves = []
        
        self.assigned_checkout_id = None
        self.entry_time_sec = 0
        
        # --- SCANGESCHWINDIGKEIT (Gleichverteilung) ---
        self.scan_duration_per_item = random.uniform(scan_speed_range[0], scan_speed_range[1])
        self.scan_time_elapsed = 0.0
        
        self.picking_timer = 0.0
        self.is_picking = False

        self._init_pathing()

    def _get_shelf_pos(self, shelf_data):
        if isinstance(shelf_data, dict):
            return QPointF(shelf_data.get("x", 0), shelf_data.get("y", 0))
        elif isinstance(shelf_data, (list, tuple)) and len(shelf_data) >= 2:
            return QPointF(shelf_data[0], shelf_data[1])
        return shelf_data

    def _init_pathing(self):
        if self.start_area:
            rx = random.uniform(self.start_area.x(), self.start_area.x() + self.start_area.width())
            ry = random.uniform(self.start_area.y(), self.start_area.y() + self.start_area.height())
            self.pos = QPointF(rx, ry)
        elif self.shopping_route:
            self.pos = QPointF(self.shopping_route[0])

        if self.all_shelves:
            num_targets = min(len(self.all_shelves), self.target_item_count)
            indices = random.sample(range(len(self.all_shelves)), num_targets)
            self.target_shelves = [self.all_shelves[i] for i in indices]

        self.path = self._build_full_shopping_path()
        
        if self.path:
            self.target_pos = self.path.pop(0)
            self.state = "FOLLOWING_ROUTE"
        else:
            self._goto_waiting_area()

    def _build_full_shopping_path(self):
        full_path = []
        start_route = self._get_nearest_route(self.pos, self.available_start_routes)
        if start_route:
            full_path.extend(start_route)

        if self.shopping_route:
            route_points = list(self.shopping_route)
            shelf_assignments = {}
            
            for shelf_data in self.target_shelves:
                shelf_pos = self._get_shelf_pos(shelf_data)
                
                best_idx = 0
                min_dist = float('inf')
                for i, rp in enumerate(route_points):
                    dist = QVector2D(shelf_pos - rp).length()
                    if dist < min_dist:
                        min_dist = dist
                        best_idx = i
                
                if best_idx not in shelf_assignments:
                    shelf_assignments[best_idx] = []
                shelf_assignments[best_idx].append(shelf_pos)

            for i, rp in enumerate(route_points):
                ox = random.uniform(-self.max_offset, self.max_offset)
                oy = random.uniform(-self.max_offset, self.max_offset)
                jittered_pos = rp + QPointF(ox, oy)
                full_path.append(jittered_pos)
                
                if i in shelf_assignments:
                    for s_pos in shelf_assignments[i]:
                        full_path.append(s_pos)
                        full_path.append(jittered_pos)

        return full_path

    def _get_nearest_route(self, current_pos, routes_dict):
        if not routes_dict:
            return []
        best_route = []
        min_dist = float('inf')
        for name, points in routes_dict.items():
            if not points: continue
            start_node = points[0]
            vec = QVector2D(start_node - current_pos)
            dist = vec.length()
            if dist < min_dist:
                min_dist = dist
                best_route = points
        return best_route

    def tick(self, dt):
        if self.state == "FOLLOWING_ROUTE":
            if self.is_picking:
                self.picking_timer += dt
                if self.picking_timer > 0.5:
                    self.picking_timer = 0
                    self.is_picking = False
                    self.item_count += 1 
            else:
                self._move_along_path(dt)
        
        elif self.state == "WALKING_TO_WAITING":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                self.state = "WAITING_AREA"
        
        elif self.state == "IN_QUEUE":
            self._move_to_target(dt)
        
        elif self.state == "SCANNING":
            self.scan_time_elapsed += dt
            if self.scan_time_elapsed >= self.scan_duration_per_item:
                self.scan_time_elapsed = 0.0
                if self.item_count > 0:
                    self.item_count -= 1
                
                if self.item_count <= 0:
                    self._finish_checkout()
        
        elif self.state == "LEAVING":
            self._move_leaving(dt)

    def _move_along_path(self, dt):
        if not self.target_pos:
            self._goto_waiting_area()
            return

        dist = self._move_to_target(dt)
        if dist < 5.0:
            is_shelf = False
            for s_data in self.target_shelves:
                s_pos = self._get_shelf_pos(s_data)
                if QVector2D(self.pos - s_pos).length() < 2.0:
                    is_shelf = True
                    break
            
            if is_shelf:
                self.is_picking = True
                self.picking_timer = 0
            
            if self.path:
                self.target_pos = self.path.pop(0)
            else:
                self._goto_waiting_area()

    def _goto_waiting_area(self):
        if self.waiting_area:
            rx = random.uniform(self.waiting_area.x(), self.waiting_area.x() + self.waiting_area.width())
            ry = random.uniform(self.waiting_area.y(), self.waiting_area.y() + self.waiting_area.height())
            self.target_pos = QPointF(rx, ry)
            self.state = "WALKING_TO_WAITING"
        else:
            self.state = "WAITING_AREA"

    def _move_to_target(self, dt):
        if not self.target_pos:
            return 0.0
        
        vec = QPointF(self.target_pos.x() - self.pos.x(), self.target_pos.y() - self.pos.y())
        dist = math.sqrt(vec.x()**2 + vec.y()**2)
        
        if dist > 0:
            dx = vec.x() / dist
            dy = vec.y() / dist
            
            # NEU: Winkel berechnen (in Grad)
            self.angle = math.degrees(math.atan2(dy, dx))
            
            move_dist = self.speed * dt
            
            if move_dist >= dist:
                self.pos = self.target_pos
                return 0.0
            else:
                self.pos = QPointF(self.pos.x() + dx * move_dist, self.pos.y() + dy * move_dist)
                return dist - move_dist
        return 0.0

    def go_to_queue(self, target_pos, checkout_id, global_exit_dir):
        self.target_pos = target_pos
        self.assigned_checkout_id = checkout_id
        self.state = "IN_QUEUE"

    def _finish_checkout(self):
        self.state = "LEAVING"
        self.scan_time_elapsed = 0.0
        
        selected_exit_route = self._get_nearest_route(self.pos, self.available_exit_routes)
        
        self.path = []
        if selected_exit_route:
            self.path = [QPointF(p) for p in selected_exit_route]
            if self.path:
                self.target_pos = self.path.pop(0)
        else:
            self.target_pos = self.pos + QPointF(200, 0)

    def _move_leaving(self, dt):
        if self.target_pos:
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if self.path:
                    self.target_pos = self.path.pop(0)
        
        if self.exit_area and self.exit_area.contains(self.pos):
            self.state = "GONE"
        elif not self.exit_area and not self.path and not self.target_pos:
             self.state = "GONE"