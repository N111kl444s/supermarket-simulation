# src/view/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QTableWidget,
    QPushButton,
    QStackedWidget,
    QListWidget,
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QCheckBox,
    QTableWidgetItem,
    QHeaderView,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter

from settings import *

# HIER: Import korrigiert und erweitert
from .render_items import (
    CustomerItem,
    CheckoutItem,
    ShelfItem,
    WaitingAreaItem,
)


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Prototyp 19: Map System (Refactored)")
        self.setGeometry(100, 100, 1400, 900)

        # State Flags für UI
        self.is_sim_maximized = False
        self.is_admin_mode = False

        self.setup_ui()

    def setup_ui(self):
        w = QWidget()
        self.setCentralWidget(w)
        main_layout = QVBoxLayout(w)

        # --- OBERE REIHE ---
        top_row = QHBoxLayout()
        top_row.addWidget(self.create_top_left(), 1)
        top_row.addWidget(self.create_top_right(), 1)
        self.top_row_widget = QWidget()
        self.top_row_widget.setLayout(top_row)
        main_layout.addWidget(self.top_row_widget, 1)

        # --- UNTERE REIHE ---
        bot_row = QHBoxLayout()
        bot_row.addWidget(self.create_bottom_left(), 1)
        bot_row.addWidget(self.create_bottom_right(), 1)
        self.bottom_row_widget = QWidget()
        self.bottom_row_widget.setLayout(bot_row)
        main_layout.addWidget(self.bottom_row_widget, 1)

    def create_top_left(self):
        gb = QGroupBox("Eingabeparameter")
        l = QVBoxLayout(gb)

        # Admin Modus Checkbox
        self.chk_admin = QCheckBox("Admin-Modus")
        self.chk_admin.toggled.connect(self.toggle_admin_mode)
        l.addWidget(self.chk_admin)

        # Stacked Widget (Sim vs Admin)
        self.stack_tl = QStackedWidget()

        # Seite 1: Sim Controls
        page_sim = QWidget()
        sl = QVBoxLayout(page_sim)
        self.spin_actors = QSpinBox()
        self.spin_actors.setValue(10)
        sl.addWidget(QLabel("Anzahl Kunden:"))
        sl.addWidget(self.spin_actors)

        self.btn_start = QPushButton("Start Simulation")
        self.btn_start.clicked.connect(
            lambda: self.controller.toggle_simulation()
        )
        sl.addWidget(self.btn_start)
        self.stack_tl.addWidget(page_sim)

        # Seite 2: Admin Controls
        page_admin = QWidget()
        al = QVBoxLayout(page_admin)
        al.addWidget(QPushButton("Route zeichnen"))
        al.addWidget(QPushButton("Regale platzieren"))
        self.stack_tl.addWidget(page_admin)

        l.addWidget(self.stack_tl)
        return gb

    def create_top_right(self):
        gb = QGroupBox("Ausgabe (Statistik)")
        # Platzhalter für Graphen
        l = QVBoxLayout(gb)
        l.addWidget(QLabel("Hier kommen die Graphen hin (PyQtGraph)"))
        return gb

    def create_bottom_left(self):
        gb = QGroupBox("Simulation")
        l = QVBoxLayout(gb)

        # Minimieren Button (für Vollbild Logik)
        self.btn_min_sim = QPushButton("Minimieren")
        self.btn_min_sim.hide()
        self.btn_min_sim.clicked.connect(self.toggle_fullscreen)
        l.addWidget(self.btn_min_sim)

        # Die Graphics Scene
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(COLOR_LIGHT_BG)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )  # Hübschere Kanten
        l.addWidget(self.view)

        return gb

    def create_bottom_right(self):
        gb = QGroupBox("Verwaltung")
        l = QVBoxLayout(gb)
        self.stack_br = QStackedWidget()

        # Tabs für Objekte
        tabs = QTabWidget()
        tabs.addTab(QListWidget(), "Routen")
        tabs.addTab(QListWidget(), "Objekte")
        self.stack_br.addWidget(tabs)

        l.addWidget(self.stack_br)
        return gb

    def toggle_admin_mode(self, checked):
        self.is_admin_mode = checked
        self.stack_tl.setCurrentIndex(1 if checked else 0)
        # Controller benachrichtigen...

    def toggle_fullscreen(self):
        self.is_sim_maximized = not self.is_sim_maximized
        if self.is_sim_maximized:
            self.top_row_widget.hide()
            self.bottom_row_widget.layout().itemAt(
                1
            ).widget().hide()  # Hide right panel
            self.btn_min_sim.show()
        else:
            self.top_row_widget.show()
            self.bottom_row_widget.layout().itemAt(1).widget().show()
            self.btn_min_sim.hide()

    def update_scene(
        self, customers, checkouts, shelves, waiting_area_rect=None
    ):
        """Zeichnet die komplette Welt basierend auf den Model-Daten."""
        self.scene.clear()

        # 1. Wartebereich (optional)
        if waiting_area_rect:
            self.scene.addItem(WaitingAreaItem(waiting_area_rect))

        # 2. Regale
        for s in shelves:
            self.scene.addItem(ShelfItem(s[0], s[1]))

        # 3. Kassen (NEU HINZUGEFÜGT)
        for c_data in checkouts:
            self.scene.addItem(CheckoutItem(c_data))

        # 4. Kunden
        for c in customers:
            item = CustomerItem(c)  # Übergibt das Datenobjekt an die Grafik
            self.scene.addItem(item)
