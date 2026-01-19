"""
Customer agent logic.
Refactored:
- Uses Pathfinding to avoid obstacles (A*).
- Uses 'get_closest_walkable' to approach shelves without entering them.
- Increased arrival distance threshold for shelves.
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D


class CustomerModel:
    def __init__(
        self,
        map_manager,
        shopping_route,
        max_offset=10,
        is_disabled=False,
        scan_speed_range=(0.5, 1.5),
        speed_walk_params=(2.5, 0.5),
        speed_roll_params=(1.5, 0.3),
        items_params=(12, 4),
    ):
        self.map_mgr = map_manager
        self.shopping_route = shopping_route

        self.max_offset = max_offset
        self.is_disabled = is_disabled

        self.pos = QPointF(0, 0)
        self.angle = 0.0

        self.state = "SPAWNING"
        self.path = []
        self.target_pos = None

        # --- Stats ---
        if self.is_disabled:
            mu, sigma = speed_roll_params
        else:
            mu, sigma = speed_walk_params
        self.speed = max(0.1, random.normalvariate(mu, sigma))

        mu_items, sigma_items = items_params
        self.target_item_count = max(
            1, int(random.normalvariate(mu_items, sigma_items))
        )
        self.item_count = 0

        self.target_shelves = []

        self.assigned_checkout_id = None
        self.entry_time_sec = 0
        self.scan_duration_per_item = random.uniform(*scan_speed_range)
        self.scan_time_elapsed = 0.0
        self.picking_timer = 0.0
        self.is_picking = False

        self._init_shopping_list()
        self._init_pathing()

    def _get_pos_from_shelf(self, s):
        return QPointF(s.get("x", 0), s.get("y", 0))

    def _init_shopping_list(self):
        shelves_by_var = self.map_mgr.get_shelves_by_variant()
        available_variants = list(shelves_by_var.keys())

        if not available_variants:
            return

        self.target_shelves = []
        wanted_variants = random.choices(
            available_variants,
            k=min(len(available_variants), self.target_item_count),
        )
        wanted_variants = list(set(wanted_variants))

        current_ref_pos = QPointF(0, 0)
        if self.map_mgr.start_area_rect:
            current_ref_pos = self.map_mgr.start_area_rect.center()
        elif self.shopping_route:
            current_ref_pos = self.shopping_route[0]

        for var in wanted_variants:
            candidates = shelves_by_var[var]
            best_s = min(
                candidates,
                key=lambda s: QVector2D(
                    self._get_pos_from_shelf(s) - current_ref_pos
                ).length(),
            )
            self.target_shelves.append(best_s)
            current_ref_pos = self._get_pos_from_shelf(best_s)

    def _init_pathing(self):
        if self.map_mgr.start_area_rect:
            r = self.map_mgr.start_area_rect
            self.pos = QPointF(
                random.uniform(r.left(), r.right()),
                random.uniform(r.top(), r.bottom()),
            )
        elif self.shopping_route:
            self.pos = QPointF(self.shopping_route[0])

        self.path = self._build_smart_path()

        if self.path:
            self.target_pos = self.path.pop(0)
            self.state = "FOLLOWING_ROUTE"
        else:
            self._goto_waiting_area()

    def _build_smart_path(self):
        full_path_points = []
        current_pos = self.pos

        # 1. To first Shop Route Point (Entrance)
        if self.map_mgr.start_routes:
            best_route = self._get_nearest_route_points(
                current_pos, self.map_mgr.start_routes
            )
            for p in best_route:
                segment = self.map_mgr.pathfinder.find_path(current_pos, p)
                full_path_points.extend(segment[1:])
                current_pos = p

        # 2. Visit Shelves
        for shelf in self.target_shelves:
            shelf_pos = self._get_pos_from_shelf(shelf)

            # FIX: Get Walkable Target NEXT to shelf, not inside
            target_walkable = self.map_mgr.pathfinder.get_closest_walkable(
                shelf_pos
            )

            segment = self.map_mgr.pathfinder.find_path(
                current_pos, target_walkable
            )
            full_path_points.extend(segment[1:])
            current_pos = target_walkable

        return full_path_points

    def _get_nearest_route_points(self, pos, routes_dict):
        if not routes_dict:
            return []
        best = []
        min_d = float("inf")
        for name, pts in routes_dict.items():
            if not pts:
                continue
            d = QVector2D(pts[0] - pos).length()
            if d < min_d:
                min_d = d
                best = pts
        return best

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

        # Check proximity to target (waypoint)
        if dist < 5.0:
            # Check if this waypoint is actually a shelf target
            hit_shelf = False
            for s_data in self.target_shelves:
                s_pos = self._get_pos_from_shelf(s_data)

                # FIX: Check distance to shelf center with larger radius
                # Shelf size is ~50, so radius is 25. +20 margin = 45.
                if QVector2D(self.pos - s_pos).length() < 45.0:
                    hit_shelf = True
                    break

            if hit_shelf and not self.is_picking:
                self.is_picking = True
                self.picking_timer = 0

            if not self.is_picking:
                if self.path:
                    self.target_pos = self.path.pop(0)
                else:
                    self._goto_waiting_area()

    def _goto_waiting_area(self):
        if self.map_mgr.waiting_area_rect:
            r = self.map_mgr.waiting_area_rect
            target = QPointF(
                random.uniform(r.left(), r.right()),
                random.uniform(r.top(), r.bottom()),
            )
            path = self.map_mgr.pathfinder.find_path(self.pos, target)
            self.path = path
            if self.path:
                self.target_pos = self.path.pop(0)
                self.state = "FOLLOWING_ROUTE"
            else:
                self.target_pos = target
                self.state = "WALKING_TO_WAITING"
        else:
            self.state = "WAITING_AREA"

    def _move_to_target(self, dt):
        if not self.target_pos:
            return 0.0
        vec = QPointF(
            self.target_pos.x() - self.pos.x(),
            self.target_pos.y() - self.pos.y(),
        )
        dist = math.sqrt(vec.x() ** 2 + vec.y() ** 2)
        if dist > 0:
            dx = vec.x() / dist
            dy = vec.y() / dist
            self.angle = math.degrees(math.atan2(dy, dx))
            move_dist = self.speed * dt
            if move_dist >= dist:
                self.pos = self.target_pos
                return 0.0
            else:
                self.pos = QPointF(
                    self.pos.x() + dx * move_dist,
                    self.pos.y() + dy * move_dist,
                )
                return dist - move_dist
        return 0.0

    def go_to_queue(self, target_pos, checkout_id, global_exit_dir):
        # We could use pathfinder here too if queue is far,
        # but queues usually have clear line of sight from waiting area.
        # Direct movement is usually fine here.
        self.target_pos = target_pos
        self.assigned_checkout_id = checkout_id
        self.state = "IN_QUEUE"

    def _finish_checkout(self):
        self.state = "LEAVING"
        self.scan_time_elapsed = 0.0

        exit_target = self.pos + QPointF(200, 0)
        if self.map_mgr.exit_area_rect:
            r = self.map_mgr.exit_area_rect
            exit_target = r.center()

        # Pathfinder to exit
        path = self.map_mgr.pathfinder.find_path(self.pos, exit_target)
        self.path = path
        if self.path:
            self.target_pos = self.path.pop(0)

    def _move_leaving(self, dt):
        if self.target_pos:
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if self.path:
                    self.target_pos = self.path.pop(0)

        if (
            self.map_mgr.exit_area_rect
            and self.map_mgr.exit_area_rect.contains(self.pos)
        ):
            self.state = "GONE"
        elif not self.path and not self.target_pos:
            self.state = "GONE"
