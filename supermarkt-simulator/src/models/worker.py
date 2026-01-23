"""
Worker Model.
Manages the logic for maintenance workers.
States: SPAWNING, MOVING_TO_TARGET, REPAIRING, LEAVING, GONE
"""

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
import random
from config import WALK_SPEED_PPS


class WorkerModel:
    def __init__(
        self,
        spawn_rect,
        target_checkout_data,
        exit_rect,
        repair_duration_range,
        max_offset=10,
    ):
        """
        :param spawn_rect: QRectF area where worker appears.
        :param target_checkout_data: Dict of the broken checkout (x, y, id).
        :param exit_rect: QRectF area where worker leaves.
        :param repair_duration_range: Tuple (min, max) seconds.
        """
        # Start Position
        sx = random.uniform(spawn_rect.left(), spawn_rect.right())
        sy = random.uniform(spawn_rect.top(), spawn_rect.bottom())
        self.pos = QPointF(sx, sy)

        self.target_checkout_id = target_checkout_data["id"]

        # Ziel: Kasse
        cx, cy = target_checkout_data["x"], target_checkout_data["y"]
        cw, ch = 100, 100  # Approx size, or pass it
        self.target_pos = QPointF(
            cx + cw / 2, cy + ch / 2
        )  # Center of checkout

        # Exit
        if exit_rect:
            ex = random.uniform(exit_rect.left(), exit_rect.right())
            ey = random.uniform(exit_rect.top(), exit_rect.bottom())
            self.exit_pos = QPointF(ex, ey)
        else:
            self.exit_pos = self.pos  # Fallback back to spawn

        self.state = "MOVING_TO_TARGET"
        self.speed = WALK_SPEED_PPS * 1.2  # Arbeiter laufen etwas schneller ;)

        # Repair Time
        self.repair_duration_total = random.uniform(*repair_duration_range)
        self.repair_timer = 0.0

        # Visual rotation
        self.rotation = 0.0

    def tick(self, dt):
        """
        Updates worker state logic.
        """
        if self.state == "GONE":
            return

        if self.state == "MOVING_TO_TARGET":
            self._move_towards(self.target_pos, dt)
            dist = (self.pos - self.target_pos).manhattanLength()
            if dist < 10.0:
                self.state = "REPAIRING"

        elif self.state == "REPAIRING":
            self.repair_timer += dt
            if self.repair_timer >= self.repair_duration_total:
                self.state = "LEAVING"
                # Actual repair logic triggers in SimulationManager via checking state

        elif self.state == "LEAVING":
            self._move_towards(self.exit_pos, dt)
            dist = (self.pos - self.exit_pos).manhattanLength()
            if dist < 10.0:
                self.state = "GONE"

    def _move_towards(self, target, dt):
        vec = QVector2D(target - self.pos)
        length = vec.length()
        if length > 0:
            direction = vec.normalized()
            # Rotation anpassen
            import math

            angle = math.degrees(math.atan2(direction.y(), direction.x()))
            self.rotation = angle

            step = direction * (self.speed * dt)
            # Nicht über das Ziel hinausschießen
            if step.length() > length:
                self.pos = target
            else:
                self.pos += step.toPointF()
