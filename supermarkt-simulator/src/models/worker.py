"""
Worker Model.
Manages the logic for maintenance workers.
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
        exact_target_pos,  # NEU: Exakte Position als Parameter
        exit_rect,
        repair_duration_range,
    ):
        # 1. Start-Position
        sx = random.uniform(spawn_rect.left(), spawn_rect.right())
        sy = random.uniform(spawn_rect.top(), spawn_rect.bottom())
        self.pos = QPointF(sx, sy)

        # 2. Ziel übernehmen
        self.target_checkout_id = target_checkout_data["id"]
        # Wir speichern eine KOPIE des Punkts, um Seiteneffekte zu vermeiden
        self.target_pos = QPointF(exact_target_pos)

        # 3. Exit festlegen
        if exit_rect:
            ex = random.uniform(exit_rect.left(), exit_rect.right())
            ey = random.uniform(exit_rect.top(), exit_rect.bottom())
            self.exit_pos = QPointF(ex, ey)
        else:
            self.exit_pos = QPointF(self.pos)

        self.state = "MOVING_TO_TARGET"
        self.speed = WALK_SPEED_PPS * 1.5

        self.repair_duration_total = random.uniform(*repair_duration_range)
        self.repair_timer = 0.0
        self.rotation = 0.0

    def tick(self, dt):
        if self.state == "GONE":
            return

        if self.state == "MOVING_TO_TARGET":
            dist = self._move_towards(self.target_pos, dt)
            if dist < 5.0:  # Präziser Radius
                self.state = "REPAIRING"

        elif self.state == "REPAIRING":
            self.repair_timer += dt
            if self.repair_timer >= self.repair_duration_total:
                self.state = "LEAVING"

        elif self.state == "LEAVING":
            dist = self._move_towards(self.exit_pos, dt)
            if dist < 5.0:
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
