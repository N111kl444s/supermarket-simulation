"""
Worker Model.
Manages the logic for maintenance workers.
Updated:
- Implements Route Following Logic.
- Calculates closest intersection point on route to target.
- Moves: Route -> Intersection -> Target -> Intersection -> Route Backwards.
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import WALK_SPEED_PPS


class WorkerModel:
    def __init__(
        self,
        spawn_rect,
        target_checkout_data,
        exact_target_pos,
        exit_rect,
        repair_duration_range,
        route_points=None,  # Liste von QPointF
    ):
        # 1. Start-Position
        sx = random.uniform(spawn_rect.left(), spawn_rect.right())
        sy = random.uniform(spawn_rect.top(), spawn_rect.bottom())
        self.pos = QPointF(sx, sy)
        self.start_pos = QPointF(sx, sy)  # Merken für Notfälle

        # 2. Ziel
        self.target_checkout_id = target_checkout_data["id"]
        self.target_pos = QPointF(exact_target_pos)

        # 3. Exit (Fallback)
        if exit_rect:
            ex = random.uniform(exit_rect.left(), exit_rect.right())
            ey = random.uniform(exit_rect.top(), exit_rect.bottom())
            self.exit_pos = QPointF(ex, ey)
        else:
            self.exit_pos = QPointF(self.pos)

        # 4. Route Analyse
        self.route_points = route_points if route_points else []
        self.current_route_index = 0
        self.intersection_index = (
            -1
        )  # Index des Punktes auf der Route, wo wir abbiegen

        # State Management
        if self.route_points:
            # Berechne den besten Abzweigpunkt (geringste Distanz zum Ziel)
            self.intersection_index = self._find_best_intersection_index(
                self.target_pos
            )
            self.state = "FOLLOWING_ROUTE_IN"
        else:
            # Fallback: Direktflug
            self.state = "MOVING_TO_TARGET_DIRECT"

        self.speed = WALK_SPEED_PPS * 1.5
        self.repair_duration_total = random.uniform(*repair_duration_range)
        self.repair_timer = 0.0
        self.rotation = 0.0

    def _find_best_intersection_index(self, target):
        """Findet den Index des Routenpunkts mit der geringsten Distanz zum Ziel."""
        if not self.route_points:
            return -1

        best_idx = 0
        min_dist = float("inf")

        for i, p in enumerate(self.route_points):
            vec = QVector2D(p - target)
            d = vec.length()
            if d < min_dist:
                min_dist = d
                best_idx = i
        return best_idx

    def tick(self, dt):
        if self.state == "GONE":
            return

        # --- HINWEG ---

        if self.state == "FOLLOWING_ROUTE_IN":
            # Wir laufen die Route Punkt für Punkt ab, bis zum Intersection Index
            if self.current_route_index <= self.intersection_index:
                if self.current_route_index < len(self.route_points):
                    next_p = self.route_points[self.current_route_index]
                    dist = self._move_towards(next_p, dt)
                    if dist < 5.0:
                        self.current_route_index += 1
                else:
                    self.state = "APPROACHING_TARGET_FROM_ROUTE"
            else:
                # Angekommen am Abzweig -> Ab zur Kasse
                self.state = "APPROACHING_TARGET_FROM_ROUTE"

        elif self.state == "APPROACHING_TARGET_FROM_ROUTE":
            dist = self._move_towards(self.target_pos, dt)
            if dist < 5.0:
                self.state = "REPAIRING"

        # --- FALLBACK (Keine Route) ---
        elif self.state == "MOVING_TO_TARGET_DIRECT":
            dist = self._move_towards(self.target_pos, dt)
            if dist < 5.0:
                self.state = "REPAIRING"

        # --- ARBEIT ---
        elif self.state == "REPAIRING":
            self.repair_timer += dt
            if self.repair_timer >= self.repair_duration_total:
                # Fertig -> Rückweg bestimmen
                if self.route_points:
                    self.state = "RETURNING_TO_ROUTE"
                    # Wir müssen zum Intersection Point zurück
                    self.current_route_index = self.intersection_index
                else:
                    self.state = "LEAVING_DIRECT"

        # --- RÜCKWEG ---

        elif self.state == "RETURNING_TO_ROUTE":
            if self.current_route_index < len(self.route_points):
                target = self.route_points[self.current_route_index]
                dist = self._move_towards(target, dt)
                if dist < 5.0:
                    self.state = "FOLLOWING_ROUTE_OUT"
                    self.current_route_index -= (
                        1  # Wir gehen rückwärts durch die Liste
                    )
            else:
                self.state = "FOLLOWING_ROUTE_OUT"

        elif self.state == "FOLLOWING_ROUTE_OUT":
            if self.current_route_index >= 0:
                target = self.route_points[self.current_route_index]
                dist = self._move_towards(target, dt)
                if dist < 5.0:
                    self.current_route_index -= 1
            else:
                # Ende der Route (Startpunkt) erreicht -> Verschwinden
                self.state = "GONE"

        elif self.state == "LEAVING_DIRECT":
            dist = self._move_towards(self.exit_pos, dt)
            if dist < 10.0:
                self.state = "GONE"

    def _move_towards(self, target, dt):
        vec = QVector2D(target - self.pos)
        dist = vec.length()
        if dist > 0:
            direction = vec.normalized()
            angle = math.degrees(math.atan2(direction.y(), direction.x()))
            self.rotation = angle

            move_step = self.speed * dt
            if move_step >= dist:
                self.pos = QPointF(target)
                return 0.0
            else:
                self.pos += (direction * move_step).toPointF()
                return dist - move_step
        return 0.0
