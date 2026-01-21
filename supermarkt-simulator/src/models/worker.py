"""
Worker (Technician) Model.
Handles pathfinding to broken checkouts via defined routes and repairs.
"""

import math
import random
from PyQt6.QtCore import QPointF, QLineF
from PyQt6.QtGui import QVector2D


class WorkerModel:
    def __init__(self, spawn_pos, worker_routes, repair_speed_range=(10, 30)):
        self.pos = spawn_pos
        self.home_pos = spawn_pos
        self.worker_routes = worker_routes
        self.speed = 3.0  # Ein Arbeiter läuft zügig
        self.state = "IDLE"  # IDLE, COMMUTE, REPAIR, RETURN

        self.current_path = []
        self.target_pos = None
        self.target_checkout_id = None

        self.repair_timer = 0.0
        self.repair_duration = 0.0
        self.repair_speed_range = repair_speed_range

        self.angle = 0.0
        self.is_fixing = False  # Für Animation

    def assign_job(self, checkout_id, checkout_pos):
        """Weist dem Techniker einen Reparaturauftrag zu."""
        self.target_checkout_id = checkout_id
        self.state = "COMMUTE"

        # Pfad berechnen: Spawn -> Route -> Closest Point to Checkout -> Checkout
        self.current_path = self._plan_path_to_checkout(checkout_pos)
        if self.current_path:
            self.target_pos = self.current_path.pop(0)
        else:
            # Fallback: Direktflug
            self.target_pos = checkout_pos

    def tick(self, dt):
        self.is_fixing = False

        if self.state == "IDLE":
            # Am Spawn warten
            self.pos = self.home_pos
            return

        elif self.state == "COMMUTE":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if self.current_path:
                    self.target_pos = self.current_path.pop(0)
                else:
                    # Am Ziel angekommen
                    self.state = "REPAIR"
                    self.repair_timer = 0.0
                    self.repair_duration = random.uniform(
                        *self.repair_speed_range
                    )

        elif self.state == "REPAIR":
            self.is_fixing = True  # Trigger Animation
            self.repair_timer += dt
            if self.repair_timer >= self.repair_duration:
                # Fertig
                self.state = "RETURN"
                self._plan_return_path()
                return True  # Signalisiert "Job Done" an SimulationManager

        elif self.state == "RETURN":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if self.current_path:
                    self.target_pos = self.current_path.pop(0)
                else:
                    self.state = "IDLE"
                    self.target_checkout_id = None

        return False

    def _move_to_target(self, dt):
        if not self.target_pos:
            return 0.0
        vec = QVector2D(self.target_pos - self.pos)
        dist = vec.length()
        if dist > 0:
            direction = vec.normalized()
            self.angle = math.degrees(math.atan2(direction.y(), direction.x()))
            move = self.speed * dt
            if move >= dist:
                self.pos = self.target_pos
                return 0.0
            else:
                self.pos = (QVector2D(self.pos) + direction * move).toPointF()
                return dist - move
        return 0.0

    def _plan_path_to_checkout(self, checkout_pos):
        """
        Findet den Punkt auf allen verfügbaren Worker-Routen,
        der der Kasse am nächsten ist.
        """
        if not self.worker_routes:
            return [checkout_pos]

        best_point = None
        min_dist_to_checkout = float("inf")
        best_route_name = None
        best_idx_on_route = -1

        # 1. Finde den "Abbiegepunkt" auf einer Route
        for r_name, points in self.worker_routes.items():
            for i, p in enumerate(points):
                # Wir konvertieren zu QVector2D für Mathe
                d = QVector2D(p - checkout_pos).length()
                if d < min_dist_to_checkout:
                    min_dist_to_checkout = d
                    best_point = p
                    best_route_name = r_name
                    best_idx_on_route = i

        if not best_point:
            return [checkout_pos]

        # 2. Baue Pfad vom Spawn (oder aktueller Pos) über Route zum Abbiegepunkt
        # Wir nehmen vereinfacht an, der Worker startet am Start der Route
        # (Eine echte Graphensuche wäre hier overkill, wir laufen einfach die Route ab)
        route_points = self.worker_routes[best_route_name]

        # Pfad: [Punkte auf Route bis Index] + [Checkout Pos]
        path = []

        # Finde nächsten Punkt auf Route zum Einstieg (einfach: Start der Route)
        # Wenn wir schon auf der Route wären, wäre es komplexer.
        # Hier: Laufe Route vom Start bis zum Abbiegepunkt
        for k in range(best_idx_on_route + 1):
            path.append(route_points[k])

        path.append(checkout_pos)
        return path

    def _plan_return_path(self):
        """Invertiert den Hinweg (ohne Pfadberechnung, da wir History nutzen könnten, aber wir berechnen neu)."""
        # Einfach: Laufe zur Home-Pos
        # Besser: Laufe zum Einstiegspunkt der Route zurück
        self.current_path = [self.home_pos]  # Fallback: Beamen/Direktlauf

        # Wenn wir einen Pfad nutzen wollen:
        # Wir sind bei Checkout. Gehe zum Abbiegepunkt zurück.
        # Dann Route rückwärts.
        # Aber der Einfachheit halber für V1: Laufe direkt zum Spawn zurück,
        # oder implementiere Rückweg analog zu Hinweg.

        # V2: Reverse Logic
        if self.worker_routes:
            # Wir nehmen an, wir haben den Hinweg gespeichert? Nein.
            # Recalculate best point
            best_point = None
            min_dist = float("inf")
            for r_name, points in self.worker_routes.items():
                for p in points:
                    d = QVector2D(p - self.pos).length()
                    if d < min_dist:
                        min_dist = d
                        best_point = p

            if best_point:
                self.current_path = [best_point, self.home_pos]
            else:
                self.current_path = [self.home_pos]
