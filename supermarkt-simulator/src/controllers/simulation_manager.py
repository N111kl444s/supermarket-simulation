"""
Simulation Manager Module.
Handles the game loop, time management, and entity lifecycle.
Updated:
- Queue Logic synchronized with VisualController (Horizontal alignment).
- Handles Left/Right orientation correctly for customer positioning.
- Uses dynamic spacing from settings.
"""

import random
import math
from PyQt6.QtCore import QTimer, QTime, QObject, pyqtSignal, QPointF
from PyQt6.QtGui import QVector2D
from models.customer import CustomerModel
from config import (
    DEFAULT_OPEN_TIME,
    DEFAULT_CLOSE_TIME,
    FACTOR_1X,
    ANIMATION_TICK_MS,
)


class SimulationManager(QObject):
    """
    Steuert den Zeitablauf und die Logik der Simulation.
    """

    time_updated = pyqtSignal(str)
    stats_updated = pyqtSignal(int, int, int)
    day_finished = pyqtSignal()
    log_message = pyqtSignal(str, str)

    def __init__(self, map_manager, settings):
        super().__init__()
        self.map_mgr = map_manager
        self.settings = settings

        self.sim_time = QTime(*DEFAULT_OPEN_TIME)
        self.open_time = QTime(*DEFAULT_OPEN_TIME)
        self.close_time = QTime(*DEFAULT_CLOSE_TIME)
        self.time_factor = FACTOR_1X
        self.time_accumulator_sec = 0.0

        self.is_running = False
        self.is_initialized = False
        self.store_is_closed_trigger = False

        self.customers_model = []
        self.checkout_queues = {}

        self.total_customers_spawned = 0

        self.target_daily_customers = 50
        self.spawn_timer_acc = 0.0
        self.next_spawn_interval = 0.0
        self.average_spawn_interval = 10.0
        self.prob_disabled = 0.1

        self.param_access_func = None

        self.sim_timer = QTimer()
        self.sim_timer.setInterval(ANIMATION_TICK_MS)
        self.sim_timer.timeout.connect(self._tick)

    def set_param_accessor(self, func):
        self.param_access_func = func

    def set_time_factor(self, factor):
        self.time_factor = factor

    def start(self):
        self.is_running = True
        self.sim_timer.start()

    def pause(self):
        self.sim_timer.stop()
        self.is_running = False

    def reset(self, open_time_val):
        self.pause()
        self.is_initialized = False
        self.customers_model.clear()
        self.checkout_queues = {}
        self.total_customers_spawned = 0
        self.store_is_closed_trigger = False

        self.sim_time = open_time_val
        self.open_time = open_time_val
        self.time_accumulator_sec = 0.0

        self.time_updated.emit(self.sim_time.toString("HH:mm"))
        self.stats_updated.emit(0, 0, 0)

    def init_day(self, target_customers, prob_disabled, open_t, close_t):
        self.target_daily_customers = target_customers
        self.prob_disabled = prob_disabled / 100.0
        self.open_time = open_t
        self.close_time = close_t
        self.sim_time = self.open_time
        self.time_accumulator_sec = 0.0
        self.total_customers_spawned = 0
        self.store_is_closed_trigger = False

        seconds_open = self.open_time.secsTo(self.close_time)
        if seconds_open <= 0:
            seconds_open = 1
        self.average_spawn_interval = seconds_open / max(
            1, self.target_daily_customers
        )
        self.spawn_timer_acc = 0.0
        self._calc_next_spawn()

        self.is_initialized = True
        self.log_message.emit(
            f"Laden geöffnet. Erwarte ca. {self.target_daily_customers} Kunden.",
            "blue",
        )

    def skip_day(self):
        self.pause()
        self.sim_time = self.close_time
        self.time_updated.emit(self.sim_time.toString("HH:mm"))
        self.log_message.emit("Tag übersprungen.", "orange")
        self.day_finished.emit()

    def _tick(self):
        real_dt = ANIMATION_TICK_MS / 1000.0
        game_dt = real_dt * self.time_factor

        self.time_accumulator_sec += game_dt
        while self.time_accumulator_sec >= 60.0:
            self.sim_time = self.sim_time.addSecs(60)
            self.time_accumulator_sec -= 60.0
            self.time_updated.emit(self.sim_time.toString("HH:mm"))

        is_closing_time = self.sim_time >= self.close_time

        if is_closing_time:
            if not self.store_is_closed_trigger:
                self.log_message.emit(
                    "Ladenschluss! Eingang geschlossen, arbeite Rest ab...",
                    "orange",
                )
                self.store_is_closed_trigger = True

            if not self.customers_model:
                self.pause()
                self.time_updated.emit(self.sim_time.toString("HH:mm"))
                self.log_message.emit(
                    "Feierabend! Alle Kunden bedient.", "red"
                )
                self.day_finished.emit()
                return
        else:
            self._attempt_spawn(game_dt)

        active_models = []
        waiting_cnt = 0

        for model in self.customers_model:
            model.tick(game_dt)
            if model.state == "WAITING_AREA":
                waiting_cnt += 1
                if model.assigned_checkout_id is None:
                    self._try_assign_checkout(model)
            elif (
                model.state == "IN_QUEUE"
                and model.assigned_checkout_id is not None
            ):
                cid = model.assigned_checkout_id
                q = self.checkout_queues.get(cid, [])
                if q and q[0] == model:
                    dist = (model.pos - model.target_pos).manhattanLength()
                    if dist < 5.0:
                        model.state = "SCANNING"
            elif (
                model.state == "LEAVING"
                and model.assigned_checkout_id is not None
            ):
                cid = model.assigned_checkout_id
                if (
                    cid in self.checkout_queues
                    and self.checkout_queues[cid]
                    and self.checkout_queues[cid][0] == model
                ):
                    self.checkout_queues[cid].pop(0)
                    self._advance_queue(cid)
                    model.assigned_checkout_id = None

            if model.state == "GONE":
                now_sec = self.open_time.secsTo(self.sim_time)
                duration = int((now_sec - model.entry_time_sec) / 60)
                self.log_message.emit(
                    f"Kunde hat Laden nach {duration} Min verlassen.", "gray"
                )
            else:
                active_models.append(model)

        self.customers_model = active_models
        self.stats_updated.emit(
            waiting_cnt,
            len(self.customers_model),
            self.total_customers_spawned,
        )

    def _attempt_spawn(self, dt_game_seconds):
        self.spawn_timer_acc += dt_game_seconds
        if self.spawn_timer_acc >= self.next_spawn_interval:
            self.spawn_timer_acc = 0
            self._spawn_single_customer()
            self._calc_next_spawn()

    def _calc_next_spawn(self):
        variance = random.uniform(0.7, 1.3)
        self.next_spawn_interval = self.average_spawn_interval * variance

    def _spawn_single_customer(self):
        route_names = list(self.map_mgr.shop_routes.keys())
        if not route_names:
            return
        r_name = random.choice(route_names)
        is_disabled = random.random() < self.prob_disabled

        if self.param_access_func:
            params = self.param_access_func(is_disabled)
        else:
            params = {
                "walk": (2.5, 0.5),
                "roll": (1.5, 0.3),
                "items": (12, 4),
                "scan": (0.5, 1.5),
            }

        if params is None:
            return
        offset = self.settings.get("customer_path_offset", 10)

        model = CustomerModel(
            self.map_mgr.shop_routes[r_name],
            self.map_mgr.all_shelves,
            self.map_mgr.start_area_rect,
            self.map_mgr.waiting_area_rect,
            exit_area_rect=self.map_mgr.exit_area_rect,
            start_routes=self.map_mgr.start_routes,
            exit_routes=self.map_mgr.exit_routes,
            max_offset=offset,
            is_disabled=is_disabled,
            speed_walk_params=params["walk"],
            speed_roll_params=params["roll"],
            items_params=params["items"],
            scan_speed_range=params["scan"],
        )
        total_seconds_today = self.open_time.secsTo(self.sim_time)
        model.entry_time_sec = total_seconds_today
        self.customers_model.append(model)

        self.total_customers_spawned += 1

        type_str = "Kunde (eingeschränkt)" if is_disabled else "Kunde"
        self.log_message.emit(f"{type_str} hat den Laden betreten.", "green")

    def _try_assign_checkout(self, model):
        candidates = []
        for c_data in self.map_mgr.checkouts_data:
            if not c_data.get("open", True):
                continue
            cid = c_data["id"]
            if len(self.checkout_queues.get(cid, [])) < c_data.get(
                "max_queue", 5
            ):
                candidates.append(cid)
        if candidates:
            chosen_id = random.choice(candidates)
            if chosen_id not in self.checkout_queues:
                self.checkout_queues[chosen_id] = []
            self.checkout_queues[chosen_id].append(model)
            self._set_queue_target(
                model, chosen_id, len(self.checkout_queues[chosen_id]) - 1
            )

    def _advance_queue(self, cid):
        if cid not in self.checkout_queues:
            return
        for idx, model in enumerate(self.checkout_queues[cid]):
            self._set_queue_target(model, cid, idx)
            if model.state != "SCANNING":
                model.state = "IN_QUEUE"

    def _set_queue_target(self, model, cid, q_index):
        c_data = next(
            (x for x in self.map_mgr.checkouts_data if x["id"] == cid), None
        )
        if not c_data:
            return

        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)

        # FIX: Use spacing from settings
        spacing = self.settings.get("dist_queue_spacing", 36)

        cx, cy = c_data["x"], c_data["y"]
        ori = c_data.get("orientation", "Right")
        c_type = c_data["type"]
        angle = c_data.get("angle", 0)

        offset_key = (
            "offset_queue_"
            + ("sb_" if c_type == "SB" else "")
            + ("left" if ori == "Left" else "right")
        )
        off = self.settings.get(offset_key, [0, 0])
        qx_local, qy_local = off[0], off[1]

        center_x = cx + cw / 2
        center_y = cy + ch / 2
        p_unrot_x = cx + qx_local
        p_unrot_y = cy + qy_local

        rad = math.radians(angle)
        tx = p_unrot_x - center_x
        ty = p_unrot_y - center_y
        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)
        start_point = QPointF(rx + center_x, ry + center_y)

        # FIX: Direction Logic must match VisualController
        if ori == "Left":
            # Left: Direction = Angle
            dir_rad = math.radians(angle)
        else:
            # Right: Direction = Angle + 180 (Opposite)
            dir_rad = math.radians(angle + 180)

        # FIX: Use cos/sin for Horizontal Queue (was -sin/cos for Vertical)
        dir_x = math.cos(dir_rad)
        dir_y = math.sin(dir_rad)

        dir_vec = QVector2D(dir_x, dir_y)
        offset_vec = dir_vec * (q_index * spacing)

        target = start_point + offset_vec.toPointF()
        model.go_to_queue(target, cid, None)
