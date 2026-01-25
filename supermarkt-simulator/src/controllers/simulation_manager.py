"""
Simulation Manager Module.
REVERTED: Worker Ziel ist wieder der Kassen-Bildschirm/Arbeitsplatz.
"""

import random
import math
import traceback
from PyQt6.QtCore import QTimer, QTime, QObject, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QVector2D
from models.customer import CustomerModel
from models.worker import WorkerModel
from config import (
    DEFAULT_OPEN_TIME,
    DEFAULT_CLOSE_TIME,
    FACTOR_1X,
    ANIMATION_TICK_MS,
)


class SimulationManager(QObject):
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
        self.active_workers = []
        self.checkout_queues = {}
        self.assigned_maintenance = {}

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
        self.active_workers.clear()
        self.checkout_queues = {}
        self.assigned_maintenance = {}
        self.total_customers_spawned = 0
        self.store_is_closed_trigger = False

        for c_data in self.map_mgr.checkouts_data:
            c_data["malfunction"] = False

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

        for c_data in self.map_mgr.checkouts_data:
            c_data["malfunction"] = False

        self.active_workers.clear()
        self.assigned_maintenance = {}
        self.is_initialized = True
        self.log_message.emit(
            f"Laden geöffnet. Erwarte ca. {self.target_daily_customers} Kunden.",
            "blue",
        )

    def _tick(self):
        try:
            real_dt = ANIMATION_TICK_MS / 1000.0
            game_dt = real_dt * self.time_factor
            self.time_accumulator_sec += game_dt
            while self.time_accumulator_sec >= 60.0:
                self.sim_time = self.sim_time.addSecs(60)
                self.time_accumulator_sec -= 60.0
                self.time_updated.emit(self.sim_time.toString("HH:mm"))

            # 1. Maintenance & Worker Logic
            self._check_maintenance()
            self._handle_workers(game_dt)

            is_closing_time = self.sim_time >= self.close_time
            if is_closing_time:
                if not self.store_is_closed_trigger:
                    self.log_message.emit(
                        "Ladenschluss! Eingang geschlossen...", "orange"
                    )
                    self.store_is_closed_trigger = True
                if not self.customers_model and not self.active_workers:
                    self.pause()
                    self.time_updated.emit(self.sim_time.toString("HH:mm"))
                    self.log_message.emit(
                        "Feierabend! Alle Kunden bedient.", "red"
                    )
                    self.day_finished.emit()
                    return
            else:
                self._attempt_spawn(game_dt)

            # Kunden Logik
            active_models = []
            waiting_cnt = 0
            current_global_params = (
                self.param_access_func(False)
                if self.param_access_func
                else None
            )

            for model in self.customers_model:
                is_stuck = False
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
                        is_stuck = True

                if not is_stuck:
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
                                        if (
                                            cust_params
                                            and "scan" in cust_params
                                        ):
                                            min_s, max_s = cust_params["scan"]
                                else:
                                    skill = c_data.get("skill", "Azubi")
                                    key = (
                                        "newbie" if skill == "Azubi" else "pro"
                                    )
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

                if (
                    model.state == "SCANNING" or model.state == "PAYING"
                ) and not is_stuck:
                    if current_global_params:
                        cid = model.assigned_checkout_id
                        c_data = next(
                            (
                                x
                                for x in self.map_mgr.checkouts_data
                                if x["id"] == cid
                            ),
                            None,
                        )
                        if c_data:
                            fail_rate = current_global_params.get(
                                (
                                    "checkout_fail_rate_sb"
                                    if c_data.get("type") == "SB"
                                    else "checkout_fail_rate_normal"
                                ),
                                0.0,
                            )
                            if random.random() < (fail_rate / 100.0) * game_dt:
                                c_data["malfunction"] = True
                                self.log_message.emit(
                                    f"⚠️ STÖRUNG an Kasse {cid}!", "red"
                                )

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

                if model.state != "GONE":
                    active_models.append(model)

            self.customers_model = active_models
            self.stats_updated.emit(
                waiting_cnt,
                len(self.customers_model),
                self.total_customers_spawned,
            )

        except Exception as e:
            print("CRITICAL ERROR IN SIMULATION TICK:")
            traceback.print_exc()

    def _get_checkout_interaction_point(self, c_data):
        """
        Berechnet den Punkt, an dem der Bildschirm/Kasse steht.
        Ziel: Exakter Punkt des Kassen-Screens (basierend auf Settings).
        """
        cw = self.settings.get("size_checkout_width", 100)
        ch = self.settings.get("size_checkout_height", 100)

        cx, cy = c_data["x"], c_data["y"]
        ori = c_data.get("orientation", "Right")
        angle = c_data.get("angle", 0)
        c_type = c_data["type"]
        is_sb = c_type == "SB"

        # REVERT: Wir nutzen wieder offset_screen_...
        suffix = "left" if ori == "Left" else "right"
        key_offset = (
            "offset_screen_sb_" + suffix
            if is_sb
            else "offset_screen_normal_" + suffix
        )

        off = self.settings.get(key_offset, [0, 0])
        lox, loy = float(off[0]), float(off[1])

        # Fallback
        if lox == 0 and loy == 0:
            lox = cw / 2
            loy = 10 if ori == "Right" else ch - 10

        center_x = cx + cw / 2
        center_y = cy + ch / 2

        p_unrot_x = cx + lox
        p_unrot_y = cy + loy

        # Rotation um Center
        rad = math.radians(angle)
        tx = p_unrot_x - center_x
        ty = p_unrot_y - center_y

        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)

        final_x = rx + center_x
        final_y = ry + center_y

        return QPointF(final_x, final_y)

    def _check_maintenance(self):
        """Prüft Kassen und spawnt Arbeiter bei Bedarf."""
        params = (
            self.param_access_func(False) if self.param_access_func else {}
        )
        repair_min = params.get("worker_repair_min", 5.0)
        repair_max = params.get("worker_repair_max", 15.0)

        spawn_rect = getattr(self.map_mgr, "worker_spawn_rect", None)
        if not spawn_rect:
            spawn_rect = self.map_mgr.start_area_rect
        if not spawn_rect:
            spawn_rect = QRectF(0, 0, 100, 100)

        for c_data in self.map_mgr.checkouts_data:
            if c_data.get("malfunction", False):
                cid = c_data["id"]
                if cid not in self.assigned_maintenance:
                    try:
                        # Berechne Zielpunkt (Screen)
                        target_pos = self._get_checkout_interaction_point(
                            c_data
                        )

                        worker = WorkerModel(
                            spawn_rect,
                            c_data,
                            target_pos,
                            self.map_mgr.exit_area_rect,
                            (repair_min, repair_max),
                        )
                        self.active_workers.append(worker)
                        self.assigned_maintenance[cid] = worker
                        self.log_message.emit(
                            f"🔧 Techniker alarmiert für Kasse {cid}.", "blue"
                        )
                    except Exception as e:
                        print(f"ERROR beim Erstellen des Workers: {e}")
                        traceback.print_exc()

    def _handle_workers(self, dt):
        alive = []
        safe_dt = min(dt, 0.1)  # Verhindert Sprünge bei Lag

        for w in self.active_workers:
            was_repairing = w.state == "REPAIRING"
            w.tick(safe_dt)

            if was_repairing and w.state == "LEAVING":
                cid = w.target_checkout_id
                c_data = next(
                    (x for x in self.map_mgr.checkouts_data if x["id"] == cid),
                    None,
                )
                if c_data:
                    c_data["malfunction"] = False
                    self.log_message.emit(
                        f"✅ Kasse {cid} wieder einsatzbereit.", "green"
                    )

                if cid in self.assigned_maintenance:
                    del self.assigned_maintenance[cid]

            if w.state != "GONE":
                alive.append(w)
        self.active_workers = alive

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
        is_disabled = random.random() < self.prob_disabled
        params = (
            self.param_access_func(is_disabled)
            if self.param_access_func
            else None
        )
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

        offset = self.settings.get("customer_path_offset", 10)
        uses_handheld = random.random() < (params.get("handheld", 0.0) / 100.0)
        ratio = params.get("pay_ratio", (30, 70))
        if random.uniform(0, 100) < ratio[0]:
            pay_method = "cash"
            pay_speed = params.get("pay_cash_speed", (3.0, 8.0))
        else:
            pay_method = "card"
            pay_speed = params.get("pay_card_speed", (1.0, 4.0))

        selected_route = (
            random.choice(list(self.map_mgr.shop_routes.values()))
            if self.map_mgr.shop_routes
            else []
        )
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
        model.entry_time_sec = self.open_time.secsTo(self.sim_time)
        self.customers_model.append(model)
        self.total_customers_spawned += 1
        self.log_message.emit(
            f"{'Kunde (eingeschränkt)' if is_disabled else 'Kunde'} betritt den Laden.",
            "green",
        )

    def _try_assign_checkout(self, model):
        candidates = [
            c["id"]
            for c in self.map_mgr.checkouts_data
            if c.get("open", True)
            and len(self.checkout_queues.get(c["id"], []))
            < c.get("max_queue", 5)
        ]
        if candidates:
            cid = random.choice(candidates)
            if cid not in self.checkout_queues:
                self.checkout_queues[cid] = []
            self.checkout_queues[cid].append(model)
            self._set_queue_target(
                model, cid, len(self.checkout_queues[cid]) - 1
            )

    def _advance_queue(self, cid):
        if cid in self.checkout_queues:
            for idx, model in enumerate(self.checkout_queues[cid]):
                self._set_queue_target(model, cid, idx)
                if model.state not in ("SCANNING", "PAYING"):
                    model.state = "IN_QUEUE"

    def _set_queue_target(self, model, cid, q_index):
        c_data = next(
            (x for x in self.map_mgr.checkouts_data if x["id"] == cid), None
        )
        if not c_data:
            return
        cw, ch = self.settings.get(
            "size_checkout_width", 100
        ), self.settings.get("size_checkout_height", 100)
        spacing = self.settings.get("dist_queue_spacing", 36)
        cx, cy = c_data["x"], c_data["y"]
        ori, c_type, angle = (
            c_data.get("orientation", "Right"),
            c_data["type"],
            c_data.get("angle", 0),
        )
        off = self.settings.get(
            "offset_queue_"
            + ("sb_" if c_type == "SB" else "")
            + ("left" if ori == "Left" else "right"),
            [0, 0],
        )
        rad = math.radians(angle)
        tx, ty = (cx + off[0]) - (cx + cw / 2), (cy + off[1]) - (cy + ch / 2)
        rx = tx * math.cos(rad) - ty * math.sin(rad)
        ry = tx * math.sin(rad) + ty * math.cos(rad)
        start_point = QPointF(rx + (cx + cw / 2), ry + (cy + ch / 2))
        dir_rad = math.radians(angle if ori == "Left" else angle + 180)
        dir_vec = QVector2D(math.cos(dir_rad), math.sin(dir_rad))
        model.go_to_queue(
            start_point + (dir_vec * (q_index * spacing)).toPointF(), cid, None
        )
