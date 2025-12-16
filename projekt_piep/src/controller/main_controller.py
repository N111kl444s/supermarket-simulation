# src/controller/main_controller.py
from PyQt6.QtCore import QTimer, QObject
from model.world import WorldState
from view.main_window import MainWindow


class MainController(QObject):
    def __init__(self):
        super().__init__()
        self.model = WorldState()
        self.view = MainWindow(self)  # View kennt Controller für Buttons

        self.timer = QTimer()
        self.timer.setInterval(30)  # SIM_TICK_MS
        self.timer.timeout.connect(self.game_loop)

        self.view.show()

    def toggle_simulation(self):
        if self.timer.isActive():
            self.timer.stop()
            self.view.btn_start.setText("Start Simulation")
        else:
            # Init Test Data if empty
            if not self.model.customers and not self.model.routes:
                # Hier würde man Maps laden
                pass

            self.timer.start()
            self.view.btn_start.setText("Stop Simulation")

    def game_loop(self):
        # 1. Logik Schritt
        self.model.tick()

        # 2. View Update
        # Wir geben die rohen Listen an die View, die sie dann rendert
        self.view.update_scene(
            self.model.customers, self.model.checkouts, self.model.shelves
        )
