"""
Simulation Manager Module.
"""

import random
import math
from PyQt6.QtCore import QTimer, QTime, QObject, pyqtSignal, QPointF
from PyQt6.QtGui import QVector2D
from models.customer import CustomerModel
from utils.distributions import sample_exponential
from config import (
    DEFAULT_OPEN_TIME,
    DEFAULT_CLOSE_TIME,
    FACTOR_1X,
    ANIMATION_TICK_MS,
)


class SimulationManager(QObject):
    time_updated = pyqtSignal(str)
    stats_updated = pyqtSignal(int, int, int)
    live_stats_updated = pyqtSignal(dict)
    stats_ready = pyqtSignal(dict)
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
        self.spawn_schedule = []
        self.spawn_index = 0
        self.prob_disabled = 0.1
        self.param_access_func = None

        self.satisfaction_store_target_min = self.settings.get(
            "satisfaction_store_target_min", 20.0
        )
        self.satisfaction_queue_target_min = self.settings.get(
            "satisfaction_queue_target_min", 5.0
        )

        self.sim_timer = QTimer()
        self.sim_timer.setInterval(ANIMATION_TICK_MS)
        self.sim_timer.timeout.connect(self._tick)

        self._live_stats_acc_sec = 0.0
        self.live_stats_cache = {}
        self._max_queue_len = 0
        self._max_queue_checkout_ids = set()
        self._max_queue_time_sec = None
        self._time_series_acc_sec = 0.0
        self._reset_statistics()

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
        self._reset_statistics()

        # Reset Malfunctions
        for c_data in self.map_mgr.checkouts_data:
            c_data["malfunction"] = False
            c_data["conflict"] = False

        self.sim_time = open_time_val
        self.open_time = open_time_val
        self.time_accumulator_sec = 0.0
        self.spawn_schedule = []
        self.spawn_index = 0
        self.time_updated.emit(self.sim_time.toString("HH:mm"))
        self.stats_updated.emit(0, 0, 0)
        self._emit_live_stats(force=True)

    def init_day(self, target_customers, prob_disabled, open_t, close_t):
        self.target_daily_customers = target_customers
        self.prob_disabled = prob_disabled / 100.0
        self.open_time = open_t
        self.close_time = close_t
        self.sim_time = self.open_time
        self.time_accumulator_sec = 0.0
        self.total_customers_spawned = 0
        self.store_is_closed_trigger = False
        self._reset_statistics()
        seconds_open = self._get_open_duration_seconds()
        self.average_spawn_interval = seconds_open / max(
            1, self.target_daily_customers
        )
        self.spawn_timer_acc = 0.0
        self.spawn_schedule = self._build_spawn_schedule(
            self.target_daily_customers, seconds_open
        )
        self.spawn_index = 0

        # Reset Malfunctions
        for c_data in self.map_mgr.checkouts_data:
            c_data["malfunction"] = False
            c_data["conflict"] = False

        self.is_initialized = True
        self.log_message.emit(
            f"Laden geöffnet. Erwarte ca. {self.target_daily_customers} Kunden.",
            "blue",
        )
        self._emit_live_stats(force=True)

    def _get_open_duration_seconds(self):
        """Return opening duration in seconds, supporting overnight and 24h."""
        seconds_open = self.open_time.secsTo(self.close_time)
        if seconds_open == 0:
            return 24 * 60 * 60
        if seconds_open < 0:
            return seconds_open + 24 * 60 * 60
        return seconds_open

    def get_open_duration_seconds(self):
        return self._get_open_duration_seconds()

    def get_elapsed_open_seconds(self, current_time=None):
        """Return seconds elapsed since open_time, supporting overnight/24h."""
        current = current_time if current_time else self.sim_time
        elapsed = self.open_time.secsTo(current)
        if elapsed < 0:
            elapsed += 24 * 60 * 60
        return elapsed

    def skip_day(self):
        self.pause()
        self.sim_time = self.close_time
        self.time_updated.emit(self.sim_time.toString("HH:mm"))
        self.log_message.emit("Tag übersprungen.", "orange")
        self._finalize_statistics()
        self.day_finished.emit()

    def _tick(self):
        real_dt = ANIMATION_TICK_MS / 1000.0
        game_dt = real_dt * self.time_factor
        self.time_accumulator_sec += game_dt
        while self.time_accumulator_sec >= 60.0:
            self.sim_time = self.sim_time.addSecs(60)
            self.time_accumulator_sec -= 60.0
            self.time_updated.emit(self.sim_time.toString("HH:mm"))

        # 1. Maintenance Logic
        self._handle_maintenance(game_dt)
        self._handle_conflicts(game_dt)

        # Only spawn new customers if store is still open (not yet closed)
        if not self.store_is_closed_trigger:
            self._attempt_spawn(game_dt)

        # Determine if store should be closed
        # Once store_is_closed_trigger is set to True, it stays True
        if not self.store_is_closed_trigger:
            # Check if we've reached closing time
            # Handle both normal hours (open < close) and overnight hours (open > close)
            if self.open_time < self.close_time:
                # Normal case: e.g., 08:00 - 20:00
                is_closing_time = self.sim_time >= self.close_time
            else:
                # Overnight case: e.g., 22:00 - 06:00
                # Store is open until it reaches close_time (next day)
                is_closing_time = (
                    self.sim_time >= self.close_time
                    and self.sim_time < self.open_time
                )

            if is_closing_time:
                self.log_message.emit(
                    "Ladenschluss! Eingang geschlossen...", "orange"
                )
                self.store_is_closed_trigger = True

        # If store is closed and no customers left, end simulation
        if self.store_is_closed_trigger and not self.customers_model:
            self.pause()
            self.time_updated.emit(self.sim_time.toString("HH:mm"))
            self.log_message.emit("Feierabend! Alle Kunden bedient.", "red")
            self._finalize_statistics()
            self.day_finished.emit()
            return

        # 2. Customers Logic
        active_models = []
        waiting_cnt = 0
        current_global_params = (
            self.param_access_func(False) if self.param_access_func else None
        )

        for model in self.customers_model:
            prev_state = model.state
            # Störungs-Check für Pausieren
            is_stuck_due_to_malfunction = False
            is_stuck_due_to_conflict = False
            if (
                model.state in ("SCANNING", "PAYING")
                and model.assigned_checkout_id is not None
            ):
                c_data = next(
                    (
                        x
                        for x in self.map_mgr.checkouts_data
                        if x["id"] == model.assigned_checkout_id
                    ),
                    None,
                )
                if c_data and c_data.get("malfunction", False):
                    is_stuck_due_to_malfunction = True
                if c_data and c_data.get("conflict", False):
                    is_stuck_due_to_conflict = True

            if (
                not is_stuck_due_to_malfunction
                and not is_stuck_due_to_conflict
            ):
                model.tick(game_dt)

            if model.state != prev_state:
                self._handle_state_transition(model, prev_state)

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
                        if model.service_start_time_sec is None:
                            model.service_start_time_sec = (
                                self.get_elapsed_open_seconds(self.sim_time)
                            )
                        model.last_checkout_id = cid
                        min_s, max_s = 1.0, 2.0
                        c_data = next(
                            (
                                x
                                for x in self.map_mgr.checkouts_data
                                if x["id"] == cid
                            ),
                            None,
                        )
                        if c_data:
                            if c_data.get("type") == "SB":
                                if self.param_access_func:
                                    cust_params = self.param_access_func(
                                        model.is_disabled
                                    )
                                    if cust_params and "scan" in cust_params:
                                        min_s, max_s = cust_params["scan"]
                            else:
                                skill = c_data.get("skill", "Azubi")
                                key = "newbie" if skill == "Azubi" else "pro"
                                if (
                                    current_global_params
                                    and "staff" in current_global_params
                                ):
                                    staff_rng = current_global_params[
                                        "staff"
                                    ].get(key)
                                    if staff_rng:
                                        min_s, max_s = staff_rng
                        model.set_scan_speed_range(min_s, max_s)

                        # Update payment duration based on checkout type
                        if current_global_params and c_data:
                            if c_data.get("type") == "SB":
                                pay_sb = current_global_params.get(
                                    "pay_sb_speed"
                                )
                                if pay_sb:
                                    model.set_payment_speed_range(*pay_sb)
                            else:
                                if model.payment_method == "cash":
                                    pay_rng = current_global_params.get(
                                        "pay_cash_speed"
                                    )
                                else:
                                    pay_rng = current_global_params.get(
                                        "pay_card_speed"
                                    )
                                if pay_rng:
                                    model.set_payment_speed_range(*pay_rng)

                        # One-time malfunction/annoyance checks per customer
                        if current_global_params and c_data:
                            if not model.malfunction_checked:
                                if c_data.get("type") == "SB":
                                    fail_rate = current_global_params.get(
                                        "checkout_fail_rate_sb", 0.0
                                    )
                                else:
                                    fail_rate = current_global_params.get(
                                        "checkout_fail_rate_normal", 0.0
                                    )
                                if (
                                    not c_data.get("malfunction", False)
                                    and random.random()
                                    < (fail_rate / 100.0)
                                ):
                                    c_data["malfunction"] = True
                                    if cid in self._stats_raw["checkouts"]:
                                        self._stats_raw["checkouts"][cid][
                                            "malfunction_events"
                                        ] += 1
                                    self.log_message.emit(
                                        f"⚠️ STÖRUNG an Kasse {cid}!", "red"
                                    )
                                model.malfunction_checked = True

                            if not model.conflict_checked:
                                annoy_rate = current_global_params.get(
                                    "customer_annoyance_rate", 0.0
                                )
                                if (
                                    not c_data.get("conflict", False)
                                    and random.random()
                                    < (annoy_rate / 100.0)
                                ):
                                    if c_data.get("malfunction", False):
                                        c_data["pending_conflict"] = True
                                    else:
                                        c_data["conflict"] = True
                                        if cid in self._stats_raw["checkouts"]:
                                            self._stats_raw["checkouts"][cid][
                                                "conflict_events"
                                            ] += 1
                                        self.log_message.emit(
                                            f"😠 Verärgerter Kunde an Kasse {cid}!",
                                            "orange",
                                        )
                                model.conflict_checked = True

            # Störung/Verärgerung werden einmalig pro Kunde beim Start des Scanvorgangs geprüft

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
                self._finalize_customer_stats(model)
            else:
                active_models.append(model)
        self.customers_model = active_models
        self.stats_updated.emit(
            waiting_cnt,
            len(self.customers_model),
            self.total_customers_spawned,
        )
        self._emit_live_stats(game_dt=game_dt)

    def _handle_maintenance(self, dt):
        """Handles checkout repairs by cashiers."""
        params = (
            self.param_access_func(False) if self.param_access_func else {}
        )
        repair_min = params.get("worker_repair_min", 5.0)
        repair_max = params.get("worker_repair_max", 15.0)

        for c_data in self.map_mgr.checkouts_data:
            if c_data.get("malfunction", False):
                if "repair_timer" not in c_data:
                    # Start repair
                    c_data["repair_duration"] = random.uniform(
                        repair_min, repair_max
                    )
                    c_data["repair_timer"] = 0.0
                    self.log_message.emit(
                        f"🔧 Kassierer repariert Kasse {c_data['id']}.", "blue"
                    )
                else:
                    # Continue repair
                    c_data["repair_timer"] += dt
                    if c_data["repair_timer"] >= c_data["repair_duration"]:
                        c_data["malfunction"] = False
                        del c_data["repair_timer"]
                        del c_data["repair_duration"]
                        self.log_message.emit(
                            f"✅ Kasse {c_data['id']} repariert.", "green"
                        )
                        if c_data.get("pending_conflict", False):
                            c_data["conflict"] = True
                            del c_data["pending_conflict"]
                            self.log_message.emit(
                                f"😠 Verärgerter Kunde an Kasse {c_data['id']}!",
                                "orange",
                            )

    def _handle_conflicts(self, dt):
        """Handles customer conflicts by cashiers."""
        params = (
            self.param_access_func(False) if self.param_access_func else {}
        )
        conflict_min = params.get(
            "worker_conflict_min", 2.0
        )  # Shorter than repairs
        conflict_max = params.get("worker_conflict_max", 8.0)

        for c_data in self.map_mgr.checkouts_data:
            if c_data.get("malfunction", False):
                continue
            if c_data.get("conflict", False):
                print(f"DEBUG: Handling conflict at checkout {c_data['id']}")
                if "conflict_timer" not in c_data:
                    # Start conflict resolution
                    c_data["conflict_duration"] = random.uniform(
                        conflict_min, conflict_max
                    )
                    c_data["conflict_timer"] = 0.0
                    self.log_message.emit(
                        f"🗣️ Kassierer löst Konflikt an Kasse {c_data['id']}.",
                        "blue",
                    )
                else:
                    # Continue resolution
                    c_data["conflict_timer"] += dt
                    if c_data["conflict_timer"] >= c_data["conflict_duration"]:
                        c_data["conflict"] = False
                        del c_data["conflict_timer"]
                        del c_data["conflict_duration"]
                        print(
                            f"DEBUG: Conflict resolved at checkout {c_data['id']}"
                        )
                        self.log_message.emit(
                            f"✅ Konflikt an Kasse {c_data['id']} gelöst.",
                            "green",
                        )

    def _attempt_spawn(self, dt_game_seconds):
        if not self.spawn_schedule:
            return
        elapsed = self.get_elapsed_open_seconds()
        while (
            self.spawn_index < len(self.spawn_schedule)
            and elapsed >= self.spawn_schedule[self.spawn_index]
        ):
            if self.total_customers_spawned >= self.target_daily_customers:
                break
            self._spawn_single_customer()
            self.spawn_index += 1

    def _calc_next_spawn(self):
        avg = max(0.1, self.average_spawn_interval)
        self.next_spawn_interval = random.expovariate(1.0 / avg)

    def _build_spawn_schedule(self, count, duration_sec):
        if count <= 0:
            return []
        if duration_sec <= 0:
            return [0.0] * count
        avg = max(0.1, duration_sec / count)
        intervals = [sample_exponential(avg) for _ in range(count)]
        total = sum(intervals)
        if total <= 0:
            step = duration_sec / count
            return [step * (i + 1) for i in range(count)]
        scale = duration_sec / total
        schedule = []
        acc = 0.0
        for dt in intervals:
            acc += dt * scale
            schedule.append(acc)
        return schedule

    def _spawn_single_customer(self):
        is_disabled = random.random() < self.prob_disabled
        if self.param_access_func:
            params = self.param_access_func(is_disabled)
        else:
            params = None

        if params is None:
            params = {
                "walk": (2.5, 0.5),
                "roll": (1.5, 0.3),
                "items": (12, 4),
                "scan": (0.5, 1.5),
                "handheld": 0,
                "pay_ratio": (30, 70),
                "pay_cash_speed": (3.0, 8.0),
                "pay_card_speed": (1.0, 4.0),
            }

        if "satisfaction_store_target_min" in params:
            self.satisfaction_store_target_min = params.get(
                "satisfaction_store_target_min", self.satisfaction_store_target_min
            )
        if "satisfaction_queue_target_min" in params:
            self.satisfaction_queue_target_min = params.get(
                "satisfaction_queue_target_min", self.satisfaction_queue_target_min
            )

        offset = self.settings.get("customer_path_offset", 10)

        prob_handheld = params.get("handheld", 0.0) / 100.0
        uses_handheld = random.random() < prob_handheld

        ratio = params.get("pay_ratio", (30, 70))
        roll = random.uniform(0, 100)
        if roll < ratio[0]:
            pay_method = "cash"
            pay_speed = params.get("pay_cash_speed", (3.0, 8.0))
        else:
            pay_method = "card"
            pay_speed = params.get("pay_card_speed", (1.0, 4.0))

        selected_route = []
        if self.map_mgr.shop_routes:
            all_routes = list(self.map_mgr.shop_routes.values())
            selected_route = random.choice(all_routes)

        model = CustomerModel(
            selected_route,
            self.map_mgr.all_shelves,
            self.map_mgr.start_area_rect,
            self.map_mgr.waiting_area_rect,
            exit_area_rect=self.map_mgr.exit_area_rect,
            start_routes=self.map_mgr.start_routes,
            exit_routes=self.map_mgr.exit_routes,
            max_offset=offset,
            is_disabled=is_disabled,
            uses_handheld=uses_handheld,
            payment_method=pay_method,
            payment_speed_range=pay_speed,
            speed_walk_params=params["walk"],
            speed_roll_params=params["roll"],
            items_params=params["items"],
            scan_speed_range=params["scan"],
        )
        model.customer_id = self.total_customers_spawned + 1
        total_seconds_today = self.get_elapsed_open_seconds()
        model.entry_time_sec = total_seconds_today
        if model.is_disabled:
            self._stats_raw["total_disabled_customers"] += 1
        else:
            self._stats_raw["total_normal_customers"] += 1
        if model.uses_handheld:
            self._stats_raw["handheld_customers"] += 1
        self.customers_model.append(model)
        self.total_customers_spawned += 1

        type_str = "Kunde"
        if is_disabled:
            type_str = "Kunde (eingeschränkt)"
        if uses_handheld:
            type_str += " [Handscanner]"

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
            if model.state != "SCANNING" and model.state != "PAYING":
                model.state = "IN_QUEUE"

    def _set_queue_target(self, model, cid, q_index):
        c_data = next(
            (x for x in self.map_mgr.checkouts_data if x["id"] == cid), None
        )
        if not c_data:
            return

        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)
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

        if ori == "Left":
            dir_rad = math.radians(angle)
        else:
            dir_rad = math.radians(angle + 180)

        dir_x = math.cos(dir_rad)
        dir_y = math.sin(dir_rad)
        dir_vec = QVector2D(dir_x, dir_y)
        offset_vec = dir_vec * (q_index * spacing)
        target = start_point + offset_vec.toPointF()
        model.go_to_queue(target, cid, None)
        if model.queue_join_time_sec is None:
            model.queue_join_time_sec = (
                self.get_elapsed_open_seconds(self.sim_time)
            )

    def _reset_statistics(self):
        self._stats_raw = {
            "store_stay_times": [],
            "queue_wait_times": [],
            "service_times": [],
            "payment_cash_times": [],
            "payment_card_times": [],
            "customers": [],
            "total_customers_served": 0,
            "total_normal_customers": 0,
            "total_disabled_customers": 0,
            "total_items_processed": 0,
            "cash_count": 0,
            "card_count": 0,
            "handheld_customers": 0,
            "time_series": [],
            "skill": {
                "newbie": {"scan_times": [], "pay_times": []},
                "pro": {"scan_times": [], "pay_times": []},
            },
            "checkouts": {},
        }
        self.stats = {"global": {}, "checkouts": {}, "events": []}
        self._init_checkout_stats()
        self._max_queue_len = 0
        self._max_queue_checkout_ids = set()
        self._max_queue_time_sec = None
        self._time_series_acc_sec = 0.0

    def _init_checkout_stats(self):
        for c_data in self.map_mgr.checkouts_data:
            cid = c_data.get("id")
            if cid is None:
                continue
            self._stats_raw["checkouts"][cid] = {
                "customers_served": 0,
                "normal_customers": 0,
                "disabled_customers": 0,
                "handheld_customers": 0,
                "total_items": 0,
                "cash_count": 0,
                "card_count": 0,
                "queue_wait_times": [],
                "service_times": [],
                "payment_cash_times": [],
                "payment_card_times": [],
                "queue_len_min": None,
                "queue_len_max": 0,
                "queue_len_sum": 0,
                "queue_len_count": 0,
                "open_time_sec": 0.0,
                "closed_time_sec": 0.0,
                "downtime_time_sec": 0.0,
                "malfunction_time_sec": 0.0,
                "conflict_time_sec": 0.0,
                "malfunction_events": 0,
                "conflict_events": 0,
            }

    def _avg(self, values):
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _min_max_avg(self, values):
        if not values:
            return {"min": 0.0, "max": 0.0, "avg": 0.0}
        return {
            "min": min(values),
            "max": max(values),
            "avg": self._avg(values),
        }

    def _normalize_duration(self, start_sec, end_sec):
        if start_sec is None or end_sec is None:
            return None
        delta = end_sec - start_sec
        if delta < 0:
            delta += 24 * 60 * 60
        return delta

    def _handle_state_transition(self, model, prev_state):
        now_sec = self.get_elapsed_open_seconds(self.sim_time)
        if model.state == "PAYING" and prev_state != "PAYING":
            if model.payment_start_time_sec is None:
                model.payment_start_time_sec = now_sec
        if model.state == "LEAVING" and prev_state != "LEAVING":
            if model.service_end_time_sec is None:
                model.service_end_time_sec = now_sec
        if model.state == "GONE" and prev_state != "GONE":
            if model.exit_time_sec is None:
                model.exit_time_sec = now_sec
        model.last_state = model.state

    def _finalize_customer_stats(self, model):
        if getattr(model, "stats_finalized", False):
            return
        now_sec = self.get_elapsed_open_seconds(self.sim_time)
        if model.exit_time_sec is None:
            model.exit_time_sec = now_sec

        store_stay = self._normalize_duration(
            model.entry_time_sec, model.exit_time_sec
        )
        queue_wait = self._normalize_duration(
            model.queue_join_time_sec, model.service_start_time_sec
        )
        service_time = self._normalize_duration(
            model.service_start_time_sec, model.service_end_time_sec
        )
        payment_time = self._normalize_duration(
            model.payment_start_time_sec, model.service_end_time_sec
        )

        if store_stay is not None:
            self._stats_raw["store_stay_times"].append(store_stay)
        if queue_wait is not None:
            self._stats_raw["queue_wait_times"].append(queue_wait)
        if service_time is not None:
            self._stats_raw["service_times"].append(service_time)

        satisfied = None
        if store_stay is not None and queue_wait is not None:
            store_min = store_stay / 60.0
            queue_min = queue_wait / 60.0
            satisfied = (
                store_min <= self.satisfaction_store_target_min
                and queue_min <= self.satisfaction_queue_target_min
            )

        self._stats_raw["customers"].append(
            {
                "id": getattr(model, "customer_id", None),
                "type": "disabled" if model.is_disabled else "normal",
                "handheld": bool(model.uses_handheld),
                "payment_method": model.payment_method,
                "items": model.target_item_count,
                "checkout_id": model.last_checkout_id,
                "entry_time_sec": model.entry_time_sec,
                "exit_time_sec": model.exit_time_sec,
                "store_stay_sec": store_stay,
                "queue_wait_sec": queue_wait,
                "service_time_sec": service_time,
                "payment_time_sec": payment_time,
                "satisfied": satisfied,
            }
        )

        self._stats_raw["total_customers_served"] += 1
        self._stats_raw["total_items_processed"] += (
            model.target_item_count
        )

        if model.payment_method == "cash":
            self._stats_raw["cash_count"] += 1
            if payment_time is not None:
                self._stats_raw["payment_cash_times"].append(payment_time)
        else:
            self._stats_raw["card_count"] += 1
            if payment_time is not None:
                self._stats_raw["payment_card_times"].append(payment_time)

        cid = model.last_checkout_id
        if cid in self._stats_raw["checkouts"]:
            c_stats = self._stats_raw["checkouts"][cid]
            c_stats["customers_served"] += 1
            if model.is_disabled:
                c_stats["disabled_customers"] += 1
            else:
                c_stats["normal_customers"] += 1
            if model.uses_handheld:
                c_stats["handheld_customers"] += 1
            c_stats["total_items"] += model.target_item_count
            if queue_wait is not None:
                c_stats["queue_wait_times"].append(queue_wait)
            if service_time is not None:
                c_stats["service_times"].append(service_time)
            if model.payment_method == "cash":
                c_stats["cash_count"] += 1
                if payment_time is not None:
                    c_stats["payment_cash_times"].append(payment_time)
            else:
                c_stats["card_count"] += 1
                if payment_time is not None:
                    c_stats["payment_card_times"].append(payment_time)

            c_data = next(
                (
                    x
                    for x in self.map_mgr.checkouts_data
                    if x.get("id") == cid
                ),
                None,
            )
            if c_data and payment_time is not None and service_time is not None:
                scan_time = max(0.0, service_time - payment_time)
                skill = c_data.get("skill", "Azubi")
                key = "newbie" if skill == "Azubi" else "pro"
                self._stats_raw["skill"][key]["scan_times"].append(
                    scan_time
                )
                self._stats_raw["skill"][key]["pay_times"].append(
                    payment_time
                )

        model.stats_finalized = True

    def _calculate_satisfaction(self, avg_store_min, avg_queue_min):
        target_store = self.satisfaction_store_target_min
        target_queue = self.satisfaction_queue_target_min
        score = 100.0
        if avg_store_min > target_store:
            score -= min(50.0, (avg_store_min - target_store) / target_store * 50)
        if avg_queue_min > target_queue:
            score -= min(50.0, (avg_queue_min - target_queue) / target_queue * 50)
        return max(0.0, min(100.0, score))

    def _emit_live_stats(self, game_dt=0.0, force=False):
        if not force:
            self._live_stats_acc_sec += game_dt
            if self._live_stats_acc_sec < 1.0:
                return
            self._live_stats_acc_sec -= 1.0

        self._time_series_acc_sec += game_dt
        if self._time_series_acc_sec >= 60.0 or force:
            self._time_series_acc_sec = 0.0
            self._stats_raw["time_series"].append(
                {
                    "time_sec": self.get_elapsed_open_seconds(self.sim_time),
                    "customers_in_store": len(self.customers_model),
                    "total_queue": sum(
                        len(q) for q in self.checkout_queues.values()
                    ),
                }
            )

        total_queue = sum(len(q) for q in self.checkout_queues.values())
        longest_queue = max([len(q) for q in self.checkout_queues.values()] or [0])
        if longest_queue > self._max_queue_len:
            self._max_queue_len = longest_queue
            self._max_queue_checkout_ids = {
                cid
                for cid, q in self.checkout_queues.items()
                if len(q) == longest_queue
            }
            self._max_queue_time_sec = self.get_elapsed_open_seconds(
                self.sim_time
            )
        elif longest_queue == self._max_queue_len and longest_queue > 0:
            self._max_queue_checkout_ids.update(
                {
                    cid
                    for cid, q in self.checkout_queues.items()
                    if len(q) == longest_queue
                }
            )
        elapsed = self.get_elapsed_open_seconds(self.sim_time)
        scheduled_open = self._get_open_duration_seconds()
        overtime = max(0.0, elapsed - scheduled_open)
        served = self._stats_raw["total_customers_served"]
        throughput = 0.0
        if elapsed > 0:
            throughput = served / (elapsed / 3600.0)

        avg_queue_wait = self._avg(self._stats_raw["queue_wait_times"]) / 60.0
        avg_store_stay = self._avg(self._stats_raw["store_stay_times"]) / 60.0
        satisfaction = self._calculate_satisfaction(
            avg_store_stay, avg_queue_wait
        )

        open_checkouts = 0
        available_checkouts = 0
        for c_data in self.map_mgr.checkouts_data:
            if c_data.get("open", True):
                open_checkouts += 1
                if not c_data.get("malfunction") and not c_data.get("conflict"):
                    available_checkouts += 1

            cid = c_data.get("id")
            if cid in self._stats_raw["checkouts"]:
                c_stats = self._stats_raw["checkouts"][cid]
                q_len = len(self.checkout_queues.get(cid, []))
                if c_stats["queue_len_min"] is None:
                    c_stats["queue_len_min"] = q_len
                c_stats["queue_len_min"] = min(c_stats["queue_len_min"], q_len)
                c_stats["queue_len_max"] = max(c_stats["queue_len_max"], q_len)
                c_stats["queue_len_sum"] += q_len
                c_stats["queue_len_count"] += 1

                if c_data.get("open", True):
                    c_stats["open_time_sec"] += game_dt
                else:
                    c_stats["closed_time_sec"] += game_dt

                if c_data.get("malfunction", False):
                    c_stats["malfunction_time_sec"] += game_dt
                    c_stats["downtime_time_sec"] += game_dt
                if c_data.get("conflict", False):
                    c_stats["conflict_time_sec"] += game_dt
                    c_stats["downtime_time_sec"] += game_dt

        self.live_stats_cache = {
            "queue_count": total_queue,
            "customers_in_store": len(self.customers_model),
            "total_customers": self.total_customers_spawned,
            "longest_queue": self._max_queue_len,
            "longest_queue_checkouts": sorted(self._max_queue_checkout_ids),
            "longest_queue_time_sec": self._max_queue_time_sec,
            "avg_wait_time_min": avg_queue_wait,
            "throughput_per_hour": throughput,
            "checkouts_open": open_checkouts,
            "checkouts_available": available_checkouts,
            "satisfaction_score": satisfaction,
            "elapsed_open_seconds": elapsed,
            "scheduled_open_seconds": scheduled_open,
            "overtime_seconds": overtime,
        }
        self.live_stats_updated.emit(self.live_stats_cache)

    def _build_statistics_dict(self):
        times = {
            "store_stay": self._min_max_avg(self._stats_raw["store_stay_times"]),
            "queue_wait": self._min_max_avg(self._stats_raw["queue_wait_times"]),
            "service_time": self._min_max_avg(self._stats_raw["service_times"]),
        }

        payment = {
            "cash_count": self._stats_raw["cash_count"],
            "card_count": self._stats_raw["card_count"],
            "cash_time": self._min_max_avg(self._stats_raw["payment_cash_times"]),
            "card_time": self._min_max_avg(self._stats_raw["payment_card_times"]),
        }

        total_customers = (
            self._stats_raw["total_normal_customers"]
            + self._stats_raw["total_disabled_customers"]
        )
        avg_items = 0.0
        if total_customers > 0:
            avg_items = (
                self._stats_raw["total_items_processed"] / total_customers
            )

        avg_store_min = times["store_stay"]["avg"] / 60.0
        avg_queue_min = times["queue_wait"]["avg"] / 60.0

        stats = {"global": {}, "checkouts": {}, "events": []}
        scheduled_open = self._get_open_duration_seconds()
        actual_open = self.get_elapsed_open_seconds(self.sim_time)
        overtime = max(0.0, actual_open - scheduled_open)

        avg_customers_by_hour = {}
        max_customers = 0
        max_customers_time_sec = None
        max_total_queue = 0
        max_total_queue_time_sec = None
        if self._stats_raw["time_series"]:
            buckets = {}
            for s in self._stats_raw["time_series"]:
                hour = int((s["time_sec"] // 3600) % 24)
                buckets.setdefault(hour, []).append(s["customers_in_store"])

                if s["customers_in_store"] > max_customers:
                    max_customers = s["customers_in_store"]
                    max_customers_time_sec = s["time_sec"]

                if s["total_queue"] > max_total_queue:
                    max_total_queue = s["total_queue"]
                    max_total_queue_time_sec = s["time_sec"]

            for h, values in buckets.items():
                avg_customers_by_hour[h] = sum(values) / len(values)

        busiest_hour = None
        if max_customers_time_sec is not None:
            busiest_hour = int((max_customers_time_sec // 3600) % 24)
        stats["global"] = {
            "total_customers_spawned": self.total_customers_spawned,
            "total_customers_served": self._stats_raw["total_customers_served"],
            "total_normal_customers": self._stats_raw["total_normal_customers"],
            "total_disabled_customers": self._stats_raw["total_disabled_customers"],
            "total_handheld_customers": self._stats_raw["handheld_customers"],
            "total_items_processed": self._stats_raw["total_items_processed"],
            "avg_items_per_customer": avg_items,
            "open_time": self.open_time.toString("HH:mm"),
            "close_time": self.close_time.toString("HH:mm"),
            "scheduled_open_seconds": scheduled_open,
            "actual_open_seconds": actual_open,
            "overtime_seconds": overtime,
            "times": {
                "store_stay_min": times["store_stay"]["min"],
                "store_stay_max": times["store_stay"]["max"],
                "store_stay_avg": times["store_stay"]["avg"],
                "queue_wait_min": times["queue_wait"]["min"],
                "queue_wait_max": times["queue_wait"]["max"],
                "queue_wait_avg": times["queue_wait"]["avg"],
                "service_time_min": times["service_time"]["min"],
                "service_time_max": times["service_time"]["max"],
                "service_time_avg": times["service_time"]["avg"],
            },
            "payment": payment,
            "satisfaction_score": self._calculate_satisfaction(
                avg_store_min, avg_queue_min
            ),
            "peak": {
                "max_queue_len": self._max_queue_len,
                "max_queue_checkouts": sorted(self._max_queue_checkout_ids),
                "max_queue_time_sec": self._max_queue_time_sec,
                "max_customers": max_customers,
                "max_customers_time_sec": max_customers_time_sec,
                "max_total_queue": max_total_queue,
                "max_total_queue_time_sec": max_total_queue_time_sec,
                "avg_customers_by_hour": avg_customers_by_hour,
                "busiest_hour": busiest_hour,
            },
        }

        for cid, c_stats in self._stats_raw["checkouts"].items():
            c_data = next(
                (
                    x
                    for x in self.map_mgr.checkouts_data
                    if x.get("id") == cid
                ),
                None,
            )
            stats["checkouts"][cid] = {
                "type": c_data.get("type", "Normal") if c_data else "Normal",
                "customers_served": c_stats["customers_served"],
                "normal_customers": c_stats["normal_customers"],
                "disabled_customers": c_stats["disabled_customers"],
                "handheld_customers": c_stats["handheld_customers"],
                "total_items": c_stats["total_items"],
                "queue_wait": self._min_max_avg(c_stats["queue_wait_times"]),
                "service_time": self._min_max_avg(c_stats["service_times"]),
                "skill": c_data.get("skill", "-") if c_data else "-",
                "queue_length": {
                    "min": c_stats["queue_len_min"]
                    if c_stats["queue_len_min"] is not None
                    else 0,
                    "max": c_stats["queue_len_max"],
                    "avg": (
                        c_stats["queue_len_sum"] / c_stats["queue_len_count"]
                        if c_stats["queue_len_count"] > 0
                        else 0.0
                    ),
                },
                "availability": {
                    "open_time_sec": c_stats["open_time_sec"],
                    "closed_time_sec": c_stats["closed_time_sec"],
                    "downtime_time_sec": c_stats["downtime_time_sec"],
                    "malfunction_time_sec": c_stats["malfunction_time_sec"],
                    "conflict_time_sec": c_stats["conflict_time_sec"],
                    "uptime_percent": (
                        (c_stats["open_time_sec"] - c_stats["downtime_time_sec"])
                        / c_stats["open_time_sec"]
                        * 100.0
                        if c_stats["open_time_sec"] > 0
                        else 0.0
                    ),
                },
                "events": {
                    "malfunction_events": c_stats["malfunction_events"],
                    "conflict_events": c_stats["conflict_events"],
                },
                "payment": {
                    "cash_count": c_stats["cash_count"],
                    "card_count": c_stats["card_count"],
                    "cash_time": self._min_max_avg(c_stats["payment_cash_times"]),
                    "card_time": self._min_max_avg(c_stats["payment_card_times"]),
                    "total_time": self._min_max_avg(
                        c_stats["payment_cash_times"]
                        + c_stats["payment_card_times"]
                    ),
                },
            }

        stats["_raw"] = {
            "store_stay_times": list(self._stats_raw["store_stay_times"]),
            "queue_wait_times": list(self._stats_raw["queue_wait_times"]),
            "service_times": list(self._stats_raw["service_times"]),
        }

        stats["customers"] = {
            "list": list(self._stats_raw["customers"]),
        }

        satisfied_count = 0
        unsatisfied_count = 0
        for c in stats["customers"]["list"]:
            if c.get("satisfied") is True:
                satisfied_count += 1
            elif c.get("satisfied") is False:
                unsatisfied_count += 1

        stats["global"]["satisfaction_targets"] = {
            "store_min": self.satisfaction_store_target_min,
            "queue_min": self.satisfaction_queue_target_min,
        }
        stats["global"]["satisfaction_split"] = {
            "satisfied": satisfied_count,
            "unsatisfied": unsatisfied_count,
        }

        stats["advanced"] = {
            "skill": {
                "newbie": {
                    "scan_time": self._min_max_avg(
                        self._stats_raw["skill"]["newbie"]["scan_times"]
                    ),
                    "pay_time": self._min_max_avg(
                        self._stats_raw["skill"]["newbie"]["pay_times"]
                    ),
                },
                "pro": {
                    "scan_time": self._min_max_avg(
                        self._stats_raw["skill"]["pro"]["scan_times"]
                    ),
                    "pay_time": self._min_max_avg(
                        self._stats_raw["skill"]["pro"]["pay_times"]
                    ),
                },
            }
        }

        newbie_avg = stats["advanced"]["skill"]["newbie"]["scan_time"]["avg"]
        pro_avg = stats["advanced"]["skill"]["pro"]["scan_time"]["avg"]
        ratio = (newbie_avg / pro_avg) if pro_avg > 0 else 0.0
        stats["advanced"]["skill"]["efficiency_ratio"] = ratio

        return stats

    def _finalize_statistics(self):
        self.stats = self._build_statistics_dict()
        self.stats_ready.emit(self.stats)

    def get_statistics_snapshot(self):
        return self._build_statistics_dict()

    def get_live_checkout_stats(self, checkout_id):
        c_data = next(
            (
                x
                for x in self.map_mgr.checkouts_data
                if x.get("id") == checkout_id
            ),
            None,
        )
        if not c_data:
            return None

        if not c_data.get("open", True):
            status = "closed"
        elif c_data.get("malfunction", False):
            status = "malfunction"
        elif c_data.get("conflict", False):
            status = "conflict"
        else:
            status = "open"

        q_len = len(self.checkout_queues.get(checkout_id, []))
        c_stats = self._stats_raw["checkouts"].get(checkout_id, {})
        service_avg = self._avg(c_stats.get("service_times", []))
        pay_avg = self._avg(
            c_stats.get("payment_cash_times", [])
            + c_stats.get("payment_card_times", [])
        )
        scan_avg = max(0.0, service_avg - pay_avg)

        cash_count = c_stats.get("cash_count", 0)
        card_count = c_stats.get("card_count", 0)
        total_pay = cash_count + card_count
        cash_percent = (cash_count / total_pay * 100.0) if total_pay else 0.0
        card_percent = (card_count / total_pay * 100.0) if total_pay else 0.0

        return {
            "status": status,
            "queue_length": q_len,
            "customers_served": c_stats.get("customers_served", 0),
            "scan_avg_sec": scan_avg,
            "pay_avg_sec": pay_avg,
            "total_items": c_stats.get("total_items", 0),
            "cash_percent": cash_percent,
            "card_percent": card_percent,
            "skill": c_data.get("skill", "-"),
            "type": c_data.get("type", "Normal"),
        }
