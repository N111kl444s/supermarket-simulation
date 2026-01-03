"""
Customer agent logic.
Refactored:
- Implements "Shopping List" logic: Customers actally walk to shelves.
- Path is constructed as: Start -> [Route -> Shelf -> Route] -> Checkout -> Exit.
- Fixed speed and scanning logic.
"""

import math
import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import WALK_SPEED_PPS, WALK_SPEED_DISABLED_FACTOR, SCAN_TIME_PER_ITEM_MS, SHELF_SIZE

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
        self.state = "SPAWNING"
        self.path = []
        self.target_pos = None
        
        # --- KORREKTE GESCHWINDIGKEIT ---
        # Wir nutzen den Basiswert aus der Config.
        base_speed = WALK_SPEED_PPS
        if self.is_disabled:
            self.speed = base_speed * WALK_SPEED_DISABLED_FACTOR
        else:
            self.speed = base_speed

        self.item_count = 0
        self.target_item_count = max(1, int(random.normalvariate(12, 4))) # Durchschnittlich 12 Items
        self.target_shelves = [] # Liste der Regale, die besucht werden sollen
        
        self.assigned_checkout_id = None
        self.entry_time_sec = 0
        
        # --- SCAN LOGIC ---
        self.scan_duration_per_item = SCAN_TIME_PER_ITEM_MS / 1000.0
        self.scan_time_elapsed = 0.0
        
        # Wenn der Kunde gerade ein Item nimmt (kurze Pause am Regal)
        self.picking_timer = 0.0
        self.is_picking = False

        self._init_pathing()

    def _init_pathing(self):
        # 1. Start Position
        if self.start_area:
            rx = random.uniform(self.start_area.x(), self.start_area.x() + self.start_area.width())
            ry = random.uniform(self.start_area.y(), self.start_area.y() + self.start_area.height())
            self.pos = QPointF(rx, ry)
        elif self.shopping_route:
            self.pos = QPointF(self.shopping_route[0])

        # 2. Einkaufsliste generieren (Zufällige Regale auswählen)
        if self.all_shelves:
            # Wähle zufällige Regale aus, maximal so viele wie target_items
            num_targets = min(len(self.all_shelves), self.target_item_count)
            # Wir nehmen Indices der Regale
            indices = random.sample(range(len(self.all_shelves)), num_targets)
            self.target_shelves = [self.all_shelves[i] for i in indices]

        # 3. Pfad berechnen (Start -> Shop + Regale -> Wartebereich)
        self.path = self._build_full_shopping_path()
        
        if self.path:
            self.target_pos = self.path.pop(0)
            self.state = "FOLLOWING_ROUTE"
        else:
            self._goto_waiting_area()

    def _build_full_shopping_path(self):
        """
        Konstruiert einen Pfad, der die Zulaufroute, die Einkaufsroute
        UND Abstecher zu den Regalen beinhaltet.
        """
        full_path = []

        # A. Zulaufroute (Nächstgelegene)
        start_route = self._get_nearest_route(self.pos, self.available_start_routes)
        if start_route:
            full_path.extend(start_route)

        # B. Einkaufsroute mit Regal-Abstechern (Zig-Zag)
        if self.shopping_route:
            # Wir kopieren die Route, damit wir sie nicht verändern
            route_points = list(self.shopping_route)
            
            # Wir ordnen jedem Regal den "besten" Punkt auf der Route zu, um abzubrechen
            # Simple Logik: Finde den Route-Punkt mit der geringsten Distanz zum Regal
            shelf_assignments = {} # {route_index: [shelf_pos, shelf_pos]}
            
            for shelf_pos in self.target_shelves:
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

            # Pfad zusammenbauen
            for i, rp in enumerate(route_points):
                # 1. Gehe zum Route-Punkt
                # Add Jitter (natürliche Bewegung)
                ox = random.uniform(-self.max_offset, self.max_offset)
                oy = random.uniform(-self.max_offset, self.max_offset)
                jittered_pos = rp + QPointF(ox, oy)
                full_path.append(jittered_pos)
                
                # 2. Falls hier Regale zugeordnet sind, gehe hin und zurück
                if i in shelf_assignments:
                    for s_pos in shelf_assignments[i]:
                        # Hin zum Regal (Exakt, ohne Jitter, damit er davor steht)
                        full_path.append(s_pos)
                        # HIER wird er später das Item nehmen (wir erkennen das an der Position)
                        
                        # Zurück zum Route-Punkt (damit er nicht durch Wände glitcht zum nächsten)
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
                # Simuliere kurzes Warten am Regal
                self.picking_timer += dt
                if self.picking_timer > 0.5: # 0.5 Sekunden pro Item greifen
                    self.picking_timer = 0
                    self.is_picking = False
                    self.item_count += 1 # Jetzt erst Item hinzufügen!
            else:
                self._move_along_path(dt)
        
        elif self.state == "WALKING_TO_WAITING":
            dist = self._move_to_target(dt)
            if dist < 5.0:
                self.state = "WAITING_AREA"
        
        elif self.state == "IN_QUEUE":
            self._move_to_target(dt)
        
        elif self.state == "SCANNING":
            # Item-by-Item Countdown
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
            # Ziel erreicht.
            # Check: Ist das ein Regal?
            # Wir prüfen einfach, ob wir an einer Position sind, die in unserer target_shelves Liste war
            # Da wir QPointF vergleichen, nutzen wir eine kleine Toleranz
            is_shelf = False
            for s in self.target_shelves:
                if QVector2D(self.pos - s).length() < 2.0:
                    is_shelf = True
                    break
            
            if is_shelf:
                self.is_picking = True
                self.picking_timer = 0
            
            # Nächster Punkt
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
        
        # Wähle näheste Ausgangsroute vom aktuellen Punkt (Kasse)
        selected_exit_route = self._get_nearest_route(self.pos, self.available_exit_routes)
        
        self.path = []
        if selected_exit_route:
            self.path = [QPointF(p) for p in selected_exit_route]
            if self.path:
                self.target_pos = self.path.pop(0)
        else:
            # Fallback: Laufe einfach nach rechts raus, wenn keine Route da ist
            self.target_pos = self.pos + QPointF(200, 0)

    def _move_leaving(self, dt):
        # Bewege zum Ziel (Routenpunkt)
        if self.target_pos:
            dist = self._move_to_target(dt)
            if dist < 5.0:
                if self.path:
                    self.target_pos = self.path.pop(0)
                # Wenn Pfad leer, bleiben wir stehen (oder gehen in Area Logik über)
        
        # Check ob in Area
        if self.exit_area and self.exit_area.contains(self.pos):
            self.state = "GONE"
        
        # Fallback Cleanup, wenn Route zu Ende und keine Area definiert
        elif not self.path and not self.target_pos:
             self.state = "GONE"