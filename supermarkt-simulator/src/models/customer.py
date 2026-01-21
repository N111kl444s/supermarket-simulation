"""
Customer agent logic.
Refactored:
- Implements a State Machine for natural shopping behavior.
- ADDED: Payment Method (Cash/Card) and PAYING state.
- ADDED: Payment Duration Logic.
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import SHELF_SIZE


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
        uses_handheld=False,
        payment_method="card",  # NEU
        payment_speed_range=(1.0, 4.0), # NEU
        scan_speed_range=(0.5, 1.5),
        speed_walk_params=(2.5, 0.5),
        speed_roll_params=(1.5, 0.3),
        items_params=(12, 4),
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
        self.uses_handheld = uses_handheld
        self.payment_method = payment_method
        self.payment_speed_range = payment_speed_range

        self.pos = QPointF(0, 0)
        self.angle = 0.0

        self.state = "SPAWNING"

        self.main_route_points = []
        self.current_route_idx = 0
        self.shelf_assignments = {}

        self.target_pos = None
        self.return_pos = None

        # --- BEWEGUNG ---
        if self.is_disabled:
            mu, sigma = speed_roll_params
        else:
            mu, sigma = speed_walk_params
        val = random.normalvariate(mu, sigma)
        self.speed = max(0.1, val)

        # --- ARTIKELANZAHL ---
        mu_items, sigma_items = items_params
        item_val = int(random.normalvariate(mu_items, sigma_items))

        self.item_count = 0
        self.target_item_count = max(1, item_val)

        self.assigned_checkout_id = None

        # --- SCAN LOGIC ---
        self.scan_speed_range = scan_speed_range
        self.current_scan_duration = random.uniform(*self.scan_speed_range)
        self.scan_time_elapsed = 0.0
        
        # --- PAYMENT LOGIC (NEU) ---
        self.current_payment_duration = random.uniform(*self.payment_speed_range)
        self.payment_time_elapsed = 0.0

        self.trigger_scan_anim = False
        self.picking_timer = 0.0
        self.is_picking = False

        self._init_position()
        self._plan_shopping_trip()

    def set_scan_speed_range(self, min_s, max_s):
        self.scan_speed_range = (min_s, max_s)
        self.current_scan_duration = random.uniform(min_s, max_s)

    def _get_shelf_pos(self, shelf_data):
        if isinstance(shelf_data, dict):
            return QPointF(shelf_data.get("x", 0), shelf_data.get("y", 0))
        elif isinstance(shelf_data, (list, tuple)) and len(shelf_data) >= 2:
            return QPointF(shelf_data[0], shelf_data[1])
        return QPointF(0, 0)

    def _init_position(self):
        if self.start_area:
            rx = random.uniform(
                self.start_area.x(),
                self.start_area.x() + self.start_area.width(),
            )
            ry = random.uniform(
                self.start_area.y(),
                self.start_area.y() + self.start_area.height(),
            )
            self.pos = QPointF(rx, ry)
        elif self.shopping_route:
            self.pos = QPointF(self.shopping_route[0])

    def _plan_shopping_trip(self):
        self.main_route_points = []
        start_route = self._get_nearest_route(self.pos, self.available_start_routes)
        if start_route:
            for p in start_route:
                pt = p if isinstance(p, QPointF) else QPointF(p[0], p[1])
                self.main_route_points.append(pt)

        shop_route_start_idx = len(self.main_route_points)
        if self.shopping_route:
            for p in self.shopping_route:
                pt = p if isinstance(p, QPointF) else QPointF(p[0], p[1])
                ox = random.uniform(-self.max_offset, self.max_offset)
                oy = random.uniform(-self.max_offset, self.max_offset)
                self.main_route_points.append(pt + QPointF(ox, oy))

        avg_items_per_visit = 1.6
        target_visits = max(1, int(self.target_item_count / avg_items_per_visit))

        chosen_shelves = []
        if self.all_shelves:
            candidates = []
            for s in self.all_shelves:
                s_pos = self._get_shelf_pos(s)
                min_dist = float("inf")
                if self.shopping_route:
                    for rp in self.shopping_route:
                        pt = rp if isinstance(rp, QPointF) else QPointF(rp[0], rp[1])
                        d = QVector2D(s_pos - pt).length()
                        if d < min_dist: min_dist = d
                candidates.append((min_dist, s))
            candidates.sort(key=lambda x: x[0])
            count = min(len(candidates), target_visits)
            chosen_shelves = [c[1] for c in candidates[:count]]

        self.shelf_assignments = {}
        if self.shopping_route:
            for shelf in chosen_shelves:
                s_pos = self._get_shelf_pos(shelf)
                best_idx = -1
                min_dist = float("inf")
                for i in range(len(self.shopping_route)):
                    real_idx = shop_route_start_idx + i
                    if real_idx < len(self.main_route_points):
                        rp = self.main_route_points[real_idx]
                        dist = QVector2D(s_pos - rp).length()
                        if dist < min_dist:
                            min_dist = dist
                            best_idx = real_idx
                if best_idx != -1:
                    if best_idx not in self.shelf_assignments:
                        self.shelf_assignments[best_idx] = []
                    self.shelf_assignments[best_idx].append(shelf)

        if self.main_route_points:
            self.current_route_idx = 0
            self.target_pos = self.main_route_points[0]
            self.state = "FOLLOWING_ROUTE"
        else:
            self._goto_waiting_area()

    def tick(self, dt):
        self.trigger_scan_anim = False

        if self.state == "FOLLOWING_ROUTE":
            self._update_following_route(dt)
        elif self.state == "GOING_TO_SHELF":
            self._update_going_to_shelf(dt)
        elif self.state == "PICKING":
            self.picking_timer += dt
            if self.picking_timer > 0.8:
                self._collect_items()
                self.is_picking = False
                self.state = "RETURNING_TO_ROUTE"
                self.target_pos = self.return_pos
        elif self.state == "RETURNING_TO_ROUTE":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                self._check_for_shelves_at_current_index()
        elif self.state == "WALKING_TO_WAITING":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                self.state = "WAITING_AREA"
        elif self.state == "IN_QUEUE":
            self._move_to_target(dt)
        elif self.state == "SCANNING":
            self._update_scanning(dt)
        elif self.state == "PAYING": # NEU
            self._update_paying(dt)
        elif self.state == "LEAVING":
            self._update_leaving(dt)

    def _update_following_route(self, dt):
        dist = self._move_to_target(dt)
        if dist < 5.0:
            if self._check_for_shelves_at_current_index():
                return
            self.current_route_idx += 1
            if self.current_route_idx < len(self.main_route_points):
                self.target_pos = self.main_route_points[self.current_route_idx]
            else:
                self._goto_waiting_area()

    def _check_for_shelves_at_current_index(self):
        if self.current_route_idx in self.shelf_assignments:
            shelves = self.shelf_assignments[self.current_route_idx]
            if shelves:
                next_shelf = shelves.pop(0)
                s_pos = self._get_shelf_pos(next_shelf)
                self.return_pos = self.main_route_points[self.current_route_idx]
                vec_to_shelf = QVector2D(s_pos - self.pos)
                length = vec_to_shelf.length()
                stop_dist = (SHELF_SIZE / 2) + 20
                if length > stop_dist:
                    offset = vec_to_shelf.normalized() * (length - stop_dist)
                    self.target_pos = self.pos + offset.toPointF()
                else:
                    self.target_pos = s_pos
                self.state = "GOING_TO_SHELF"
                return True
            if not shelves:
                del self.shelf_assignments[self.current_route_idx]
                if self.state == "RETURNING_TO_ROUTE":
                    self.state = "FOLLOWING_ROUTE"
                    self.current_route_idx += 1
                    if self.current_route_idx < len(self.main_route_points):
                        self.target_pos = self.main_route_points[self.current_route_idx]
                    else:
                        self._goto_waiting_area()
                    return True
        if self.state == "RETURNING_TO_ROUTE":
            self.state = "FOLLOWING_ROUTE"
            self.current_route_idx += 1
            if self.current_route_idx < len(self.main_route_points):
                self.target_pos = self.main_route_points[self.current_route_idx]
            else:
                self._goto_waiting_area()
        return False

    def _update_going_to_shelf(self, dt):
        dist = self._move_to_target(dt)
        if dist < 5.0:
            self.state = "PICKING"
            self.picking_timer = 0.0

    def _collect_items(self):
        r = random.random()
        if r < 0.50: count = 1
        elif r < 0.90: count = 2
        else: count = 3
        self.item_count += count

    def _update_scanning(self, dt):
        self.scan_time_elapsed += dt
        if self.scan_time_elapsed >= self.current_scan_duration:
            self.scan_time_elapsed = 0.0
            self.trigger_scan_anim = True
            self.current_scan_duration = random.uniform(*self.scan_speed_range)

            if self.uses_handheld:
                # Handheld direkt zum Bezahlen
                self.state = "PAYING"
                self.payment_time_elapsed = 0.0
            else:
                if self.item_count > 0:
                    self.item_count -= 1
                if self.item_count <= 0:
                    self.state = "PAYING"
                    self.payment_time_elapsed = 0.0

    def _update_paying(self, dt):
        self.payment_time_elapsed += dt
        
        # Visuelles Feedback (grüner Flash) auch beim Bezahlen
        if self.payment_time_elapsed < dt * 1.5:
             self.trigger_scan_anim = True
             
        if self.payment_time_elapsed >= self.current_payment_duration:
            self._finish_checkout()

    def _update_leaving(self, dt):
        if self.target_pos:
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if hasattr(self, "exit_path") and self.exit_path:
                    self.target_pos = self.exit_path.pop(0)
        if self.exit_area and self.exit_area.contains(self.pos):
            self.state = "GONE"
        elif not self.exit_area and not hasattr(self, "exit_path") and not self.target_pos:
            self.state = "GONE"

    def _goto_waiting_area(self):
        if self.waiting_area:
            rx = random.uniform(self.waiting_area.x(), self.waiting_area.x() + self.waiting_area.width())
            ry = random.uniform(self.waiting_area.y(), self.waiting_area.y() + self.waiting_area.height())
            self.target_pos = QPointF(rx, ry)
            self.state = "WALKING_TO_WAITING"
        else:
            self.state = "WAITING_AREA"

    def _move_to_target(self, dt):
        if not self.target_pos: return 0.0
        vec = QPointF(self.target_pos.x() - self.pos.x(), self.target_pos.y() - self.pos.y())
        dist = math.sqrt(vec.x() ** 2 + vec.y() ** 2)
        if dist > 0:
            dx = vec.x() / dist; dy = vec.y() / dist
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
        self.target_pos = target_pos; self.assigned_checkout_id = checkout_id; self.state = "IN_QUEUE"

    def _finish_checkout(self):
        self.state = "LEAVING"; self.scan_time_elapsed = 0.0
        selected_exit_route = self._get_nearest_route(self.pos, self.available_exit_routes)
        self.exit_path = []
        if selected_exit_route:
            for p in selected_exit_route:
                pt = p if isinstance(p, QPointF) else QPointF(p[0], p[1])
                self.exit_path.append(pt)
            if self.exit_path: self.target_pos = self.exit_path.pop(0)
        else:
            self.target_pos = self.pos + QPointF(200, 0)

    def _get_nearest_route(self, current_pos, routes_dict):
        if not routes_dict: return []
        best_route = []; min_dist = float("inf")
        for name, points in routes_dict.items():
            if not points: continue
            start_node = points[0] if isinstance(points[0], QPointF) else QPointF(points[0][0], points[0][1])
            vec = QVector2D(start_node - current_pos)
            dist = vec.length()
            if dist < min_dist:
                min_dist = dist; best_route = points
        return best_route