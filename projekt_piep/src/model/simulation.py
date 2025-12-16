# src/model/simulation.py

import simpy
import random
import numpy as np
from typing import List, Dict, Optional, Generator

# Absolute imports
from model.entities import Customer, CheckoutLane, CustomerStatus, CashierType


class SimulationModel:
    def __init__(self):
        self.env: Optional[simpy.Environment] = None
        self.checkouts: Dict[int, CheckoutLane] = {}
        self.checkout_resources: Dict[int, simpy.Resource] = {}
        self.customers: List[Customer] = []
        self.active_customers: List[Customer] = []
        self.customer_counter = 0
        self.is_running = False

    def setup(self, checkout_configs: List[CheckoutLane]):
        self.env = simpy.Environment()
        self.checkouts = {c.id: c for c in checkout_configs}
        self.checkout_resources = {}
        self.customers = []
        self.active_customers = []
        self.customer_counter = 0

        for c in checkout_configs:
            self.checkout_resources[c.id] = simpy.Resource(
                self.env, capacity=1
            )

        self.env.process(self._customer_generator())
        self.is_running = True

    def step(self, duration: float = 0.03):
        if self.is_running and self.env:
            self.env.run(until=self.env.now + duration)

    def _customer_generator(self) -> Generator:
        while True:
            # Zufall 1: Ankunft (Exponential)
            yield self.env.timeout(random.expovariate(1.0 / 2.0))

            self.customer_counter += 1
            # Zufall 2: Artikel (Normal)
            items = int(max(1, np.random.normal(15, 5)))

            cust = Customer(
                id=self.customer_counter,
                arrival_time=self.env.now,
                total_items=items,
            )
            self.customers.append(cust)
            self.active_customers.append(cust)

            self.env.process(self._customer_process(cust))

    def _customer_process(self, customer: Customer) -> Generator:
        # 1. Shopping Time (kurz)
        customer.status = CustomerStatus.SHOPPING
        yield self.env.timeout(2.0)

        # 2. Kasse wählen
        lid = self._choose_best_checkout()
        if lid is None:
            customer.status = CustomerStatus.DONE
            return

        customer.target_lane_id = lid
        customer.status = CustomerStatus.IN_QUEUE

        res = self.checkout_resources[lid]
        lane = self.checkouts[lid]

        # 3. Anstellen
        with res.request() as request:
            yield request

            # 4. Scannen (Mit Animation!)
            customer.status = CustomerStatus.SCANNING
            customer.start_service_time = self.env.now

            # Wir simulieren das Scannen Artikel für Artikel für den visuellen Effekt
            # Zeit pro Item berechnen (in Minuten -> Sekunden)
            time_per_item = 60.0 / lane.items_per_minute

            while customer.scanned_items < customer.total_items:
                yield self.env.timeout(time_per_item)
                customer.scanned_items += 1

            # 5. Bezahlen (Gleichverteilung)
            pay_time = random.uniform(5.0, 15.0)
            yield self.env.timeout(pay_time)

            customer.end_service_time = self.env.now
            customer.status = CustomerStatus.DONE

            # Aufräumen (optional, damit Liste nicht explodiert)
            if customer in self.active_customers:
                # Wir lassen ihn noch kurz "rauslaufen" (Done State wird im Controller behandelt)
                pass

    def _choose_best_checkout(self) -> Optional[int]:
        if not self.checkout_resources:
            return None
        # Wähle Kasse mit kürzester Schlange
        return min(
            self.checkout_resources.keys(),
            key=lambda k: len(self.checkout_resources[k].queue),
        )
