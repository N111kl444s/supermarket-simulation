# src/model/world.py
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from settings import *


@dataclass
class CustomerData:
    """Reines Datenobjekt für einen Kunden (Trennung von Logik und GUI)."""

    id: int
    x: float
    y: float
    inventory: int = 0
    items_scanned: int = 0
    state: str = (
        "WALKING_ROUTE"  # WALKING_ROUTE, SHOPPING, IN_QUEUE, SCANNING, LEAVING, GONE
    )

    # Pfadfindung & Verhalten
    route_points: List[Tuple[float, float]] = field(default_factory=list)
    current_wp_idx: int = 0
    target_x: float = 0.0
    target_y: float = 0.0
    wait_ticks: int = 0
    assigned_checkout_id: Optional[int] = None
    scan_progress_ticks: int = 0
    return_pos: Optional[Tuple[float, float]] = None

    @property
    def scan_ticks_total(self):
        return int(SCAN_TIME_PER_ITEM_MS / SIM_TICK_MS)


class WorldState:
    """
    Hält den kompletten Zustand der Simulation.
    Ersetzt die Datenhaltung, die früher im MainWindow war.
    """

    def __init__(self):
        self.customers: List[CustomerData] = []
        self.checkouts: List[dict] = (
            []
        )  # Die Kassen-Daten (Dictionaries wie im Original)
        self.shelves: List[Tuple[float, float]] = []
        self.routes: Dict[str, List[Tuple[float, float]]] = {}
        self.waiting_area_rect: Optional[Tuple[float, float, float, float]] = (
            None  # x, y, w, h
        )

        self.checkout_queues: Dict[int, List[CustomerData]] = {}
        self.queue_counter = 0  # Für Statistiken

    def add_customer(self, route_points):
        if not route_points:
            return

        c = CustomerData(
            id=random.randint(1000, 9999),
            x=route_points[0][0],
            y=route_points[0][1],
            route_points=route_points,
        )
        c.target_x = route_points[1][0] if len(route_points) > 1 else c.x
        c.target_y = route_points[1][1] if len(route_points) > 1 else c.y
        self.customers.append(c)

    def tick(self):
        """Die zentrale Simulations-Schleife (Logik pur)."""
        active_customers = []
        waiting_count = 0

        for c in self.customers:
            self.update_customer(c)

            if c.state == "FINISHED_SHOPPING":
                waiting_count += 1
                self.assign_checkout(c)

            # Queue-Logik
            if c.state == "IN_QUEUE" and c.assigned_checkout_id is not None:
                self.process_queue_movement(c)

            if c.state == "LEAVING" and c.assigned_checkout_id is not None:
                self.release_checkout(c)

            if c.state != "GONE":
                active_customers.append(c)

        self.customers = active_customers
        return waiting_count

    def update_customer(self, c: CustomerData):
        """Die alte 'CustomerItem.tick()' Logik, aber ohne GUI-Code."""
        if c.state == "SCANNING":
            if c.items_scanned < c.inventory:
                c.scan_progress_ticks += 1
                if c.scan_progress_ticks >= c.scan_ticks_total:
                    c.items_scanned += 1
                    c.scan_progress_ticks = 0
            else:
                c.state = "LEAVING"
            return

        if c.state == "LEAVING":
            c.y -= WALK_SPEED
            if c.y < -50:
                c.state = "GONE"
            return

        # Bewegung zum Ziel
        dx = c.target_x - c.x
        dy = c.target_y - c.y
        dist = math.hypot(dx, dy)

        if dist < WALK_SPEED:
            c.x = c.target_x
            c.y = c.target_y
            self.handle_target_reached(c)
        else:
            # Normalisieren und bewegen
            factor = WALK_SPEED / dist
            c.x += dx * factor
            c.y += dy * factor

        # Warte-Logik (z.B. am Regal oder im Wartebereich)
        if c.state in ["FINISHED_SHOPPING", "WAITING_AT_SHELF"]:
            c.wait_ticks -= 1
            if c.wait_ticks <= 0:
                if c.state == "FINISHED_SHOPPING":
                    self.new_wait_target(c)
                elif c.state == "WAITING_AT_SHELF":
                    c.state = "WALKING_ROUTE"  # Vereinfacht zurück zur Route
                    # Hier müsste eigentlich die 'return_pos' Logik hin
                    if c.return_pos:
                        c.target_x, c.target_y = c.return_pos
                        c.state = "RETURNING_TO_ROUTE"

    def handle_target_reached(self, c: CustomerData):
        if c.state == "WALKING_TO_SHELF":
            c.state = "WAITING_AT_SHELF"
            c.wait_ticks = 50
            if random.random() < ITEM_PICK_PROBABILITY:
                c.inventory += 1

        elif c.state == "WALKING_ROUTE":
            c.current_wp_idx += 1
            if c.current_wp_idx >= len(c.route_points):
                c.state = "FINISHED_SHOPPING"
                self.new_wait_target(c)
            else:
                c.target_x = c.route_points[c.current_wp_idx][0]
                c.target_y = c.route_points[c.current_wp_idx][1]

                # Chance auf Regalbesuch (Original Logik)
                if self.shelves and random.random() < SHELF_PROBABILITY:
                    shelf = self.find_nearest_shelf(c.x, c.y)
                    if shelf:
                        c.return_pos = (c.target_x, c.target_y)
                        c.target_x, c.target_y = shelf
                        c.state = "WALKING_TO_SHELF"

    def new_wait_target(self, c):
        if self.waiting_area_rect:
            x, y, w, h = self.waiting_area_rect
            c.target_x = random.uniform(x, x + w)
            c.target_y = random.uniform(y, y + h)
            c.wait_ticks = random.randint(50, 150)

    def find_nearest_shelf(self, x, y):
        if not self.shelves:
            return None
        return min(self.shelves, key=lambda s: math.hypot(s[0] - x, s[1] - y))

    def assign_checkout(self, c):
        # Einfache Zuweisung (wie im Original)
        if c.assigned_checkout_id is None:
            candidates = [
                chk for chk in self.checkouts if chk.get("open", True)
            ]
            # Filter Logic here...
            if candidates:
                chosen = random.choice(candidates)
                cid = chosen["id"]
                if cid not in self.checkout_queues:
                    self.checkout_queues[cid] = []
                self.checkout_queues[cid].append(c)
                c.assigned_checkout_id = cid

                # Ziel setzen (Ende der Schlange)
                self.update_queue_positions(cid)

    def process_queue_movement(self, c):
        # Prüfen ob wir ganz vorne sind
        q = self.checkout_queues.get(c.assigned_checkout_id, [])
        if q and q[0] == c:
            dist = math.hypot(c.target_x - c.x, c.target_y - c.y)
            if dist < 5.0:
                c.state = "SCANNING"

    def release_checkout(self, c):
        cid = c.assigned_checkout_id
        if cid in self.checkout_queues and self.checkout_queues[cid]:
            if self.checkout_queues[cid][0] == c:
                self.checkout_queues[cid].pop(0)
                self.update_queue_positions(cid)
                c.assigned_checkout_id = None

    def update_queue_positions(self, cid):
        # Berechnet die Zielpositionen für ALLE in der Schlange neu
        # (Hier käme die Offset-Logik aus den Settings rein)
        pass  # Platzhalter, muss mit Settings verknüpft werden
