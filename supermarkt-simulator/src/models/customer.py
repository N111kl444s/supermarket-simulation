"""
Logic model for a single customer agent.
"""

import random
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QVector2D
from config import *


class CustomerModel:
    """
    Represents the state and behavioral logic of a customer in the simulation.

    Operates as a state machine.

    @ivar pos: Current absolute position of the customer.
    @type pos: QPointF
    @ivar state: Current state (e.g., 'WALKING_ROUTE', 'SHOPPING').
    @type state: str
    @ivar inventory: Number of items collected.
    @type inventory: int
    """

    def __init__(self, rp, sp, wr):
        """
        Initializes the customer model.

        @param rp: List of route waypoints.
        @type rp: list[QPointF]
        @param sp: List of shelf positions.
        @type sp: list[QPointF]
        @param wr: Rectangle defining the waiting area.
        @type wr: QRectF
        """
        self.route = rp
        self.shelves = sp
        self.waiting_area = wr
        self.state = "WALKING_ROUTE"
        self.current_waypoint_idx = 0
        self.wait_ticks = 0
        self.return_pos = None
        self.target_pos = QPointF(0, 0)
        self.assigned_checkout_id = None
        self.inventory = 0
        self.items_scanned = 0
        self.scan_progress_ticks = 0
        self.scan_ticks_total = int(SCAN_TIME_PER_ITEM_MS / SIM_TICK_MS)
        self.pos = QPointF(0, 0)

        if rp:
            self.pos = rp[0]
            self.target_pos = rp[1] if len(rp) > 1 else self.pos

    def set_pos(self, p):
        """
        Updates the customer's position.

        @param p: New position.
        @type p: QPointF
        """
        self.pos = p

    def tick(self):
        """
        Executes one simulation step.

        Updates the state and position based on current targets and environment.
        """
        if self.state == "SCANNING":
            self.process_scanning()
            return
        if self.state == "LEAVING":
            self.set_pos(QPointF(self.pos.x(), self.pos.y() - WALK_SPEED))
            if self.pos.y() < -50:
                self.state = "GONE"
            return
        if self.state == "IN_QUEUE":
            dist = (QVector2D(self.target_pos) - QVector2D(self.pos)).length()
            if dist > 1.0:
                self.move_towards_target()
            return
        if self.state == "FINISHED_SHOPPING":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                self.new_wait_target()
            self.move_towards_target()
            return
        if self.state == "WAITING_AT_SHELF":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                self.state = "RETURNING_TO_ROUTE"
                self.target_pos = self.return_pos
            return
        self.move_towards_target()

    def process_scanning(self):
        """
        Simulates the item scanning process at a checkout.
        """
        if self.items_scanned < self.inventory:
            self.scan_progress_ticks += 1
            if self.scan_progress_ticks >= self.scan_ticks_total:
                self.items_scanned += 1
                self.scan_progress_ticks = 0
        else:
            self.state = "LEAVING"

    def new_wait_target(self):
        """
        Selects a random target position within the waiting area.
        """
        if self.waiting_area:
            self.target_pos = QPointF(
                random.uniform(
                    self.waiting_area.left(), self.waiting_area.right()
                ),
                random.uniform(
                    self.waiting_area.top(), self.waiting_area.bottom()
                ),
            )
            self.wait_ticks = random.randint(50, 150)

    def move_towards_target(self):
        """
        Moves the customer towards self.target_pos using WALK_SPEED.
        """
        curr = QVector2D(self.pos)
        tgt = QVector2D(self.target_pos)
        dist = (tgt - curr).length()
        if dist < WALK_SPEED:
            self.set_pos(self.target_pos)
            self.handle_target_reached()
        else:
            self.set_pos(
                (curr + (tgt - curr).normalized() * WALK_SPEED).toPointF()
            )

    def handle_target_reached(self):
        """
        Handles logic when the customer reaches their target position.
        Transitions states (e.g., from WALKING to WAITING).
        """
        if (
            self.state == "FINISHED_SHOPPING"
            or self.state == "IN_QUEUE"
            or self.state == "WALKING_TO_QUEUE"
        ):
            if self.state == "WALKING_TO_QUEUE":
                self.state = "IN_QUEUE"
            return
        if self.state == "WALKING_TO_SHELF":
            self.state = "WAITING_AT_SHELF"
            self.wait_ticks = 50
            if random.random() < ITEM_PICK_PROBABILITY:
                self.inventory += 1
        elif self.state == "RETURNING_TO_ROUTE":
            self.state = "WALKING_ROUTE"
            self.next_wp()
        elif self.state == "WALKING_ROUTE":
            if (
                self.current_waypoint_idx < len(self.route) - 1
                and self.shelves
                and random.random() < SHELF_PROBABILITY
            ):
                sh = self.find_nearest_shelf()
                if sh:
                    self.state = "WALKING_TO_SHELF"
                    self.return_pos = self.target_pos
                    self.target_pos = sh
                    return
            self.next_wp()

    def next_wp(self):
        """
        Advances to the next waypoint in the route.
        """
        self.current_waypoint_idx += 1
        if self.current_waypoint_idx >= len(self.route):
            self.enter_waiting_area()
        else:
            self.target_pos = self.route[self.current_waypoint_idx]

    def enter_waiting_area(self):
        """
        Transitions the customer to the waiting area state.
        """
        self.state = "FINISHED_SHOPPING"
        self.wait_ticks = 0

    def find_nearest_shelf(self):
        """
        Finds the closest shelf to the current position.

        @return: Position of the nearest shelf or None.
        @rtype: QPointF
        """
        if not self.shelves:
            return None
        return min(
            self.shelves,
            key=lambda s: (QVector2D(s) - QVector2D(self.pos)).length(),
            default=None,
        )

    def go_to_queue(self, target_pos, checkout_id):
        """
        Directs the customer to a specific checkout queue.

        @param target_pos: The target position in the queue.
        @type target_pos: QPointF
        @param checkout_id: ID of the assigned checkout.
        @type checkout_id: int
        """
        self.state = "WALKING_TO_QUEUE"
        self.target_pos = target_pos
        self.assigned_checkout_id = checkout_id
