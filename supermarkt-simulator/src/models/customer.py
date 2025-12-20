"""
Logic for the customer agent.
Refactored: Uses 'item_count' as dynamic inventory accumulator. Start Area logic verified.
"""

import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import WALK_SPEED_PPS, SCAN_TIME_PER_ITEM_MS, SHELF_PROBABILITY


class CustomerModel:
    def __init__(
        self,
        route_points,
        all_shelves,
        start_area_rect,
        waiting_area_rect,
        max_offset=0,
    ):
        self.route = list(route_points)
        self.all_shelves = list(all_shelves)  # Expecting QPointF or dict
        self.start_area = start_area_rect
        self.waiting_area = waiting_area_rect
        self.max_offset = max_offset

        # -- 1. SPAWN POSITION --
        self.pos = QPointF(0, 0)

        # Priority: Start Area -> First Route Point -> Origin
        if self.start_area:
            wx = random.uniform(
                self.start_area.left(), self.start_area.right()
            )
            wy = random.uniform(
                self.start_area.top(), self.start_area.bottom()
            )
            self.pos = QPointF(wx, wy)
        elif self.route:
            self.pos = self.route[0]

        # -- 2. SHOPPING MAPPING --
        self.shopping_map = self._map_shelves_to_route()

        # DYNAMIC ITEM COUNT
        # Starts at 0, increases when visiting shelves
        self.item_count = 0

        # Movement State
        self.route_index = 0
        self.target_pos = None
        self.state = "SPAWNING"
        self.spawn_timer = random.uniform(0.5, 2.0)

        # Random path jitter
        self.offset_vec = QVector2D(
            random.uniform(-self.max_offset, self.max_offset),
            random.uniform(-self.max_offset, self.max_offset),
        )

        # Checkout State
        self.assigned_checkout_id = None
        self.checkout_exit_direction = "Right"
        self.wait_timer = 0.0

        self.scan_duration_per_item = SCAN_TIME_PER_ITEM_MS / 1000.0
        self.total_scan_duration = 0.0
        self.scan_time_elapsed = 0.0
        self.items_scanned = 0

    def _map_shelves_to_route(self):
        mapping = {}
        if not self.route or not self.all_shelves:
            return mapping

        potential_stops = []
        for shelf_obj in self.all_shelves:
            # Handle both QPointF and dict (legacy support)
            if isinstance(shelf_obj, dict):
                shelf_pos = QPointF(shelf_obj["x"], shelf_obj["y"])
            else:
                shelf_pos = shelf_obj

            best_idx = -1
            min_dist = float("inf")
            for i, route_pt in enumerate(self.route):
                dist = (QVector2D(shelf_pos) - QVector2D(route_pt)).length()
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i

            if best_idx != -1 and min_dist < 300:
                potential_stops.append((best_idx, shelf_pos))

        for idx, pos in potential_stops:
            if idx not in mapping:
                if random.random() < SHELF_PROBABILITY:
                    mapping[idx] = pos

        return mapping

    def get_current_route_point_with_offset(self):
        if self.route_index < len(self.route):
            return self.route[self.route_index] + self.offset_vec.toPointF()
        return None

    def go_to_queue(self, target, checkout_id, exit_direction):
        self.state = "IN_QUEUE"
        self.assigned_checkout_id = checkout_id
        self.checkout_exit_direction = exit_direction
        self.target_pos = target

        # Calculate duration based on accumulated items
        self.total_scan_duration = (
            self.item_count * self.scan_duration_per_item
        )

    def tick(self, dt_seconds):
        if self.state == "GONE":
            return

        # --- SPAWNING ---
        if self.state == "SPAWNING":
            self.spawn_timer -= dt_seconds
            if self.spawn_timer <= 0:
                # Decide next target: First route point
                self.route_index = 0
                self.target_pos = self.get_current_route_point_with_offset()
                if not self.target_pos:
                    self.state = "MOVING_TO_WAITING_AREA"
                else:
                    self.state = "FOLLOWING_ROUTE"
            return

        # --- SHOPPING INTERACTION ---
        if self.state == "PICKING_ITEM":
            self.wait_timer -= dt_seconds
            if self.wait_timer <= 0:
                # Add items to cart dynamically
                picked = random.randint(1, 3)
                self.item_count += picked

                self.route_index += 1
                self.target_pos = self.get_current_route_point_with_offset()

                if self.target_pos:
                    self.state = "FOLLOWING_ROUTE"
                else:
                    self.state = "MOVING_TO_WAITING_AREA"
                    self._set_waiting_target()
            return

        # --- CHECKOUT PROCESS ---
        if self.state == "SCANNING":
            self.scan_time_elapsed += dt_seconds
            if self.scan_duration_per_item > 0:
                # Calculate progress for current item
                if self.scan_time_elapsed >= self.scan_duration_per_item:
                    self.scan_time_elapsed = 0.0
                    self.item_count -= 1
                    if self.item_count <= 0:
                        self.state = "LEAVING"
                        # Determine exit vector based on global setting
                        exit_vec = QPointF(0, 0)
                        d = self.checkout_exit_direction
                        if d == "Links":
                            exit_vec = QPointF(-100, 0)
                        elif d == "Rechts":
                            exit_vec = QPointF(100, 0)
                        elif d == "Oben":
                            exit_vec = QPointF(0, -100)
                        elif d == "Unten":
                            exit_vec = QPointF(0, 100)
                        else:
                            # Fallback
                            exit_vec = QPointF(100, 0)

                        self.target_pos = self.pos + exit_vec
            return

        # --- MOVEMENT ENGINE ---
        if self.target_pos:
            current_vec = QVector2D(self.pos)
            target_vec = QVector2D(self.target_pos)
            direction = target_vec - current_vec
            distance = direction.length()
            step = WALK_SPEED_PPS * dt_seconds

            if distance <= step:
                self.pos = self.target_pos

                if self.state == "FOLLOWING_ROUTE":
                    if self.route_index in self.shopping_map:
                        self.target_pos = self.shopping_map[self.route_index]
                        self.state = "MOVING_TO_SHELF"
                    else:
                        self.route_index += 1
                        self.target_pos = (
                            self.get_current_route_point_with_offset()
                        )
                        if not self.target_pos:
                            self.state = "MOVING_TO_WAITING_AREA"
                            self._set_waiting_target()

                elif self.state == "MOVING_TO_SHELF":
                    self.state = "PICKING_ITEM"
                    self.wait_timer = random.uniform(1.0, 3.0)

                elif self.state == "MOVING_TO_WAITING_AREA":
                    self.state = "WAITING_AREA"
                    self.target_pos = None

                elif self.state == "LEAVING":
                    self.state = "GONE"

            else:
                if distance > 0:
                    direction.normalize()
                    self.pos = (current_vec + (direction * step)).toPointF()

    def _set_waiting_target(self):
        if self.waiting_area:
            wx = random.uniform(
                self.waiting_area.left(), self.waiting_area.right()
            )
            wy = random.uniform(
                self.waiting_area.top(), self.waiting_area.bottom()
            )
            self.target_pos = QPointF(wx, wy)
        else:
            self.target_pos = self.pos
