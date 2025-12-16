import sys
import json
import random
import math
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QLabel,
    QTextEdit,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QSlider,
    QComboBox,
    QCheckBox,
    QGraphicsObject,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
)

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QRectF,
    QObject,
    QPointF,
    QTimer,
    QLineF,
)
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPixmap,
    QPainterPath,
    QVector2D,
)

import pyqtgraph as pg

# --- Pfade ---
SCRIPT_FILE = Path(__file__).resolve()
SRC_DIR = SCRIPT_FILE.parent
BASE_DIR = SRC_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"

# --- Farben ---
COLOR_ORANGE = QColor("#FF6A00")
COLOR_TURQUOISE = QColor("#00B0D0")
COLOR_GREEN = QColor("#50C878")
COLOR_DARK_TEXT = QColor("#333333")
COLOR_LIGHT_BG = QColor("#F8F8F8")
COLOR_WHITE_BG = QColor("#FFFFFF")
COLOR_BORDER = QColor("#E0E0E0")
COLOR_SHELF = QColor("#3F51B5")  # Indigo für Regale
COLOR_CUSTOMER = QColor("#E91E63")  # Pink für Kunden
COLOR_ROUTE_DEBUG = QColor(
    100, 100, 100, 100
)  # Halbtransparentes Grau für Routen

# --- KONSTANTEN ---
SHELF_SIZE = 20
CUSTOMER_SIZE = 12
SIM_TICK_MS = 30  # Ca. 30 FPS
SHELF_PROBABILITY = 0.3  # 30% Wahrscheinlichkeit
WALK_SPEED = 3.0  # Pixel pro Tick

# --- Hilfsklassen UI ---


class ClickableGroupBox(QGroupBox):
    clicked = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ClickablePixmapItem(QGraphicsObject):
    clicked = pyqtSignal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap

    def boundingRect(self):
        return QRectF(self.pixmap.rect())

    def paint(self, painter: QPainter, option, widget=None):
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class AutoFitGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.scene() and not self.sceneRect().isEmpty():
            main_window = self.window()
            if (
                main_window
                and hasattr(main_window, "is_q1_maximized")
                and main_window.is_q1_maximized
                and main_window.item_q1
            ):
                self.fitInView(
                    main_window.item_q1.boundingRect(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
            else:
                self.fitInView(
                    self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
                )


# --- SIMULATIONS-KLASSEN ---


class ShelfItem(QGraphicsRectItem):
    """Repräsentiert ein Regal in der Szene."""

    def __init__(self, x, y):
        # Zentriert um x, y
        super().__init__(
            x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
        )
        self.setBrush(QBrush(COLOR_SHELF))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(5)
        # Standardmäßig unsichtbar (wird von MainWindow gesteuert)
        self.setVisible(False)


class CustomerItem(QGraphicsEllipseItem):
    """
    Ein Kunde mit Zustandsautomat für Bewegung.
    """

    def __init__(self, route_points, all_shelves_pos):
        super().__init__(
            -CUSTOMER_SIZE / 2,
            -CUSTOMER_SIZE / 2,
            CUSTOMER_SIZE,
            CUSTOMER_SIZE,
        )
        self.setBrush(QBrush(COLOR_CUSTOMER))
        self.setPen(QPen(Qt.GlobalColor.white))
        self.setZValue(20)

        self.route = route_points  # Liste von QPointF
        self.shelves = all_shelves_pos

        # Zustand
        self.current_waypoint_idx = 0
        self.state = "WALKING_ROUTE"  # WALKING_ROUTE, WALKING_TO_SHELF, WAITING, RETURNING_TO_ROUTE, FINISHED
        self.wait_ticks = 0
        self.return_pos = (
            None  # Punkt auf der Route, zu dem zurückgekehrt wird
        )

        # Startposition (Erster Punkt der Route)
        if self.route:
            self.setPos(self.route[0])
            # Ziel ist der nächste Punkt (falls vorhanden)
            if len(self.route) > 1:
                self.current_waypoint_idx = 1
                self.target_pos = self.route[1]
            else:
                self.state = "FINISHED"  # Route zu kurz

    def tick(self):
        if self.state == "FINISHED":
            return

        if self.state == "WAITING":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                # Warten vorbei -> Zurück zur Route
                self.state = "RETURNING_TO_ROUTE"
                self.target_pos = self.return_pos
            return

        # Bewegung berechnen
        current_pos = QVector2D(self.pos())
        target = QVector2D(self.target_pos)
        direction = target - current_pos
        distance = direction.length()

        if distance < WALK_SPEED:
            # Ziel erreicht (snap to target)
            self.setPos(self.target_pos)
            self.handle_target_reached()
        else:
            # Weiterlaufen
            direction.normalize()
            new_pos = current_pos + direction * WALK_SPEED
            self.setPos(new_pos.toPointF())

    def handle_target_reached(self):
        if self.state == "WALKING_TO_SHELF":
            # Am Regal angekommen -> Warten
            self.state = "WAITING"
            sec = random.uniform(1.0, 5.0)
            self.wait_ticks = int((sec * 1000) / SIM_TICK_MS)

        elif self.state == "RETURNING_TO_ROUTE":
            # Zurück am Wegpunkt -> Weiter auf der Route
            self.state = "WALKING_ROUTE"
            # Jetzt erst den Index erhöhen, um zum NÄCHSTEN Punkt zu gehen
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.route):
                self.state = "FINISHED"
            else:
                self.target_pos = self.route[self.current_waypoint_idx]

        elif self.state == "WALKING_ROUTE":
            # Einen Routenpunkt erreicht.
            # Chance auf Ablenkung prüfen (aber nicht am allerletzten Punkt)
            if self.current_waypoint_idx < len(self.route) - 1:
                if self.shelves and random.random() < SHELF_PROBABILITY:
                    shelf = self.find_nearest_shelf()
                    if shelf:
                        self.state = "WALKING_TO_SHELF"
                        self.return_pos = (
                            self.target_pos
                        )  # Merken, wo wir waren (aktueller WP)
                        self.target_pos = shelf
                        return  # Ablauf unterbrechen, wir gehen zum Regal

            # Wenn keine Ablenkung, direkt zum nächsten Punkt
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.route):
                self.state = "FINISHED"
            else:
                self.target_pos = self.route[self.current_waypoint_idx]

    def find_nearest_shelf(self):
        if not self.shelves:
            return None
        closest_pos = None
        min_dist = float("inf")
        current = QVector2D(self.pos())
        for s_pos in self.shelves:
            dist = (QVector2D(s_pos) - current).length()
            if dist < min_dist:
                min_dist = dist
                closest_pos = s_pos
        return closest_pos


# --- SZENE ---


class RouteEditorScene(QGraphicsScene):
    clicked_point = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None

    def mousePressEvent(self, event):
        if self.main_window and self.main_window.is_admin_mode:
            if (
                self.main_window.is_drawing_mode
                or self.main_window.is_placing_shelves
            ):
                if event.button() == Qt.MouseButton.LeftButton:
                    pos = event.scenePos()
                    if self.sceneRect().contains(pos):
                        self.clicked_point.emit(pos)
                        event.accept()
                        return
        super().mousePressEvent(event)


# --- MAIN WINDOW ---


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototyp 8: Erweiterte Simulation")
        self.setGeometry(100, 100, 1400, 900)

        # Zustände
        self.is_sim_maximized = False
        self.is_q1_maximized = False
        self.is_admin_mode = False
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.show_debug_overlays = False  # Toggle für Routen/Regale

        # Daten
        self.routes_file = BASE_DIR / "routes.json"
        self.shelves_file = BASE_DIR / "shelves.json"

        self.all_routes = {}
        self.all_shelves = []
        self.current_route_points = []

        # Simulation
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulation_tick)
        self.customers = []
        self.queue_count = 0

        # Items
        self.item_q1 = None
        self.item_q2 = None
        self.item_q3 = None
        self.item_q4 = None
        self.current_route_path_item = None
        self.current_route_point_items = []
        self.shelf_items = []
        self.route_debug_items = []  # Liste aller Routen-Linien (grau)
        self.scene_rect = QRectF()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(self.top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)

        self.top_left_group_box = self.create_top_left_quadrant()
        self.top_right_group_box = self.create_top_right_quadrant()
        top_row_layout.addWidget(self.top_left_group_box, 1)
        top_row_layout.addWidget(self.top_right_group_box, 1)

        self.bottom_row_widget = QWidget()
        bottom_row_layout = QHBoxLayout(self.bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_left_group_box = self.create_bottom_left_quadrant()
        self.bottom_right_group_box = self.create_bottom_right_quadrant()
        bottom_row_layout.addWidget(self.bottom_left_group_box, 1)
        bottom_row_layout.addWidget(self.bottom_right_group_box, 1)

        main_layout.addWidget(self.top_row_widget, 1)
        main_layout.addWidget(self.bottom_row_widget, 1)

    def create_top_left_quadrant(self):
        group_box = QGroupBox("Eingabeparameter")
        layout = QVBoxLayout(group_box)

        self.admin_mode_checkbox = QCheckBox("Admin-Modus")
        self.admin_mode_checkbox.toggled.connect(self.toggle_admin_mode)
        layout.addWidget(self.admin_mode_checkbox)

        self.top_left_stack = QStackedWidget()
        layout.addWidget(self.top_left_stack)

        # --- Sim Widget ---
        sim_widget = QWidget()
        sim_layout = QFormLayout(sim_widget)

        self.sim_name_input = QLineEdit("Simulation_01")
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(5)
        self.actor_count_input.setRange(1, 200)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 500)
        self.speed_slider.setValue(150)

        self.start_sim_button = QPushButton("Simulation starten")
        self.start_sim_button.setObjectName("StartButton")
        self.start_sim_button.clicked.connect(self.toggle_simulation)

        sim_layout.addRow("Name:", self.sim_name_input)
        sim_layout.addRow("Kunden-Anzahl:", self.actor_count_input)
        sim_layout.addRow("Geschwindigkeit:", self.speed_slider)
        sim_layout.addRow(self.start_sim_button)

        # --- Admin Widget ---
        admin_widget = QWidget()
        admin_layout = QVBoxLayout(admin_widget)

        # <<< NEU: Sichtbarkeits-Toggle >>>
        self.chk_show_debug = QCheckBox("Regale & Routen anzeigen")
        self.chk_show_debug.toggled.connect(self.toggle_debug_view)

        self.new_route_button = QPushButton("Neue Route zeichnen")
        self.new_route_button.clicked.connect(self.start_drawing_mode)

        self.place_shelves_button = QPushButton("Regale platzieren")
        self.place_shelves_button.clicked.connect(self.start_shelf_mode)

        admin_layout.addWidget(self.chk_show_debug)
        admin_layout.addWidget(self.new_route_button)
        admin_layout.addWidget(self.place_shelves_button)
        admin_layout.addStretch()

        self.top_left_stack.addWidget(sim_widget)
        self.top_left_stack.addWidget(admin_widget)

        return group_box

    def create_top_right_quadrant(self):
        group_box = QGroupBox("Ausgabe & Analyse")
        layout = QVBoxLayout(group_box)
        values_layout = QFormLayout()

        self.lbl_runtime = QLabel("0.00 s")
        self.lbl_queue_count = QLabel("0")

        values_layout.addRow("Gesamtlaufzeit:", self.lbl_runtime)
        values_layout.addRow("Kunden im Kassenbereich:", self.lbl_queue_count)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        layout.addLayout(values_layout)
        layout.addWidget(self.plot_widget)
        return group_box

    def create_bottom_left_quadrant(self):
        group_box = ClickableGroupBox("Live-Simulation (Miniatur)")
        group_box.clicked.connect(self.toggle_simulation_fullscreen)
        layout = QVBoxLayout(group_box)

        self.minimize_sim_button = QPushButton(
            "Zurück zur 4-Quadranten-Ansicht"
        )
        self.minimize_sim_button.setObjectName("MinimizeButton")
        self.minimize_sim_button.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        self.minimize_sim_button.hide()
        layout.addWidget(self.minimize_sim_button)

        self.minimize_q1_button = QPushButton("Zurück zur Supermarkt-Ansicht")
        self.minimize_q1_button.setObjectName("MinimizeButton")
        self.minimize_q1_button.clicked.connect(self.toggle_q1_fullscreen)
        self.minimize_q1_button.hide()
        layout.addWidget(self.minimize_q1_button)

        # Admin Toolbar
        self.admin_toolbar = QWidget()
        tb_layout = QHBoxLayout(self.admin_toolbar)
        tb_layout.setContentsMargins(0, 5, 0, 5)

        self.btn_admin_save = QPushButton("Speichern")
        self.btn_admin_save.clicked.connect(self.finish_admin_action)
        self.btn_admin_cancel = QPushButton("Abbrechen")
        self.btn_admin_cancel.clicked.connect(self.cancel_admin_action)

        tb_layout.addWidget(self.btn_admin_save)
        tb_layout.addWidget(self.btn_admin_cancel)
        layout.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        # Szene
        self.sim_scene = RouteEditorScene(self)
        self.sim_scene.main_window = self
        self.sim_scene.clicked_point.connect(self.handle_scene_click)
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))

        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        layout.addWidget(self.sim_view)

        try:
            QUAD_WIDTH, QUAD_HEIGHT = 800, 450
            path_q1 = str(IMAGE_DIR / "quadrant_1.png")
            path_q2 = str(IMAGE_DIR / "quadrant_2.png")
            path_q3 = str(IMAGE_DIR / "quadrant_3.png")
            path_q4 = str(IMAGE_DIR / "quadrant_4.png")

            self.item_q1 = ClickablePixmapItem(QPixmap(path_q1))
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(self.toggle_q1_fullscreen)

            self.item_q2 = self.sim_scene.addPixmap(QPixmap(path_q2))
            self.item_q2.setPos(QUAD_WIDTH, 0)
            self.item_q3 = self.sim_scene.addPixmap(QPixmap(path_q3))
            self.item_q3.setPos(0, QUAD_HEIGHT)
            self.item_q4 = self.sim_scene.addPixmap(QPixmap(path_q4))
            self.item_q4.setPos(QUAD_WIDTH, QUAD_HEIGHT)

            self.scene_rect = QRectF(0, 0, QUAD_WIDTH * 2, QUAD_HEIGHT * 2)
            self.sim_scene.setSceneRect(self.scene_rect)
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

        except Exception as e:
            self.sim_scene.addText(f"Fehler Bild laden: {e}")

        return group_box

    def create_bottom_right_quadrant(self):
        group_box = QGroupBox("Zukünftige Anforderungen")
        self.bottom_right_stack = QStackedWidget(group_box)
        layout = QVBoxLayout(group_box)
        layout.addWidget(self.bottom_right_stack)

        txt = QTextEdit("Hier ist Platz für Anforderungen...")
        txt.setReadOnly(True)

        list_container = QWidget()
        lc_layout = QVBoxLayout(list_container)
        self.route_list_widget = QListWidget()
        self.route_list_widget.itemClicked.connect(self.show_route_details)
        btn_del = QPushButton("Route löschen")
        btn_del.clicked.connect(self.delete_selected_route)
        lc_layout.addWidget(QLabel("Gespeicherte Routen:"))
        lc_layout.addWidget(self.route_list_widget)
        lc_layout.addWidget(btn_del)

        self.bottom_right_stack.addWidget(txt)
        self.bottom_right_stack.addWidget(list_container)
        return group_box

    # --- DATEN & VISUALISIERUNG ---

    def load_data(self):
        # Routen laden
        if self.routes_file.exists():
            try:
                with open(self.routes_file, "r") as f:
                    data = json.load(f)
                    self.all_routes = {
                        k: [QPointF(p[0], p[1]) for p in v]
                        for k, v in data.items()
                    }
                self.route_list_widget.clear()
                for name in self.all_routes:
                    self.route_list_widget.addItem(name)
                self.draw_all_routes_debug()  # Debug-Linien erstellen (aber unsichtbar)
            except Exception as e:
                print(f"Routes Error: {e}")

        # Regale laden
        if self.shelves_file.exists():
            try:
                with open(self.shelves_file, "r") as f:
                    data = json.load(f)
                    self.all_shelves = [QPointF(p[0], p[1]) for p in data]
                self.draw_shelves()
            except Exception as e:
                print(f"Shelves Error: {e}")

    def save_shelves(self):
        data = [[p.x(), p.y()] for p in self.all_shelves]
        with open(self.shelves_file, "w") as f:
            json.dump(data, f)

    def draw_shelves(self):
        # Alte löschen
        for item in self.shelf_items:
            self.sim_scene.removeItem(item)
        self.shelf_items.clear()

        # Neue zeichnen
        for pos in self.all_shelves:
            shelf = ShelfItem(pos.x(), pos.y())
            # Sichtbarkeit abhängig vom Toggle oder Platzierungs-Modus
            is_visible = self.show_debug_overlays or self.is_placing_shelves
            shelf.setVisible(is_visible)

            self.sim_scene.addItem(shelf)
            self.shelf_items.append(shelf)

    def draw_all_routes_debug(self):
        """Zeichnet alle Routen grau im Hintergrund (versteckt)."""
        for item in self.route_debug_items:
            self.sim_scene.removeItem(item)
        self.route_debug_items.clear()

        pen = QPen(COLOR_ROUTE_DEBUG, 2)
        pen.setStyle(Qt.PenStyle.DotLine)

        for name, points in self.all_routes.items():
            if len(points) > 1:
                path = QPainterPath()
                path.moveTo(points[0])
                for p in points[1:]:
                    path.lineTo(p)
                path_item = QGraphicsPathItem(path)
                path_item.setPen(pen)
                path_item.setZValue(4)  # Unter Regalen
                path_item.setVisible(self.show_debug_overlays)  # Sichtbarkeit
                self.sim_scene.addItem(path_item)
                self.route_debug_items.append(path_item)

    def toggle_debug_view(self, checked):
        """Schaltet Regale und Routenlinien an/aus."""
        self.show_debug_overlays = checked

        # Regale updaten
        for shelf in self.shelf_items:
            shelf.setVisible(checked)

        # Routen updaten
        for route_item in self.route_debug_items:
            route_item.setVisible(checked)

    # --- ADMIN INTERAKTION ---

    def toggle_admin_mode(self, checked):
        self.is_admin_mode = checked
        if checked:
            if self.is_q1_maximized:
                self.toggle_q1_fullscreen()
            if self.is_sim_maximized:
                self.toggle_simulation_fullscreen()

            self.top_left_stack.setCurrentIndex(1)
            self.bottom_right_stack.setCurrentIndex(1)
            self.bottom_left_group_box.setTitle("Routen-Editor")

            self.bottom_left_group_box.setEnabled(False)
            if self.item_q1:
                self.item_q1.setEnabled(False)
        else:
            self.cancel_admin_action()
            self.top_left_stack.setCurrentIndex(0)
            self.bottom_right_stack.setCurrentIndex(0)
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            self.bottom_left_group_box.setEnabled(True)
            if self.item_q1:
                self.item_q1.setEnabled(True)

            # Debug-View ausmachen, wenn man Admin verlässt (optional)
            self.chk_show_debug.setChecked(False)

    def start_drawing_mode(self):
        self.is_drawing_mode = True
        self.setup_admin_fullscreen("Route zeichnen")

        self.current_route_points = []
        pen = QPen(COLOR_ORANGE, 3)
        pen.setStyle(Qt.PenStyle.DashLine)
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(pen)
        self.sim_scene.addItem(self.current_route_path_item)

        # Routen sichtbar machen zur Orientierung? Hier optional:
        # self.toggle_debug_view(True)

    def start_shelf_mode(self):
        self.is_placing_shelves = True
        self.setup_admin_fullscreen("Regale platzieren")
        # Regale müssen sichtbar sein, um sie zu sehen
        for shelf in self.shelf_items:
            shelf.setVisible(True)

    def setup_admin_fullscreen(self, title):
        self.top_row_widget.hide()
        self.bottom_right_group_box.hide()
        self.admin_toolbar.show()

        self.bottom_left_group_box.setTitle(f"Routen-Editor ({title})")
        self.bottom_left_group_box.setEnabled(True)

    def cancel_admin_action(self):
        was_placing_shelves = self.is_placing_shelves
        self.is_drawing_mode = False
        self.is_placing_shelves = False

        # Aufräumen
        if self.current_route_path_item:
            self.sim_scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for item in self.current_route_point_items:
            self.sim_scene.removeItem(item)
        self.current_route_point_items.clear()

        # UI Wiederherstellen
        self.admin_toolbar.hide()
        self.top_row_widget.show()
        self.bottom_right_group_box.show()
        self.bottom_left_group_box.setTitle("Routen-Editor")
        self.bottom_left_group_box.setEnabled(False)

        # Sichtbarkeit zurücksetzen
        if was_placing_shelves:
            # Regale wieder verstecken, falls Debug aus ist
            for shelf in self.shelf_items:
                shelf.setVisible(self.show_debug_overlays)

    def finish_admin_action(self):
        if self.is_drawing_mode:
            if self.current_route_points:
                name = f"Route_{len(self.all_routes) + 1}"
                self.all_routes[name] = list(self.current_route_points)

                data = {
                    k: [[p.x(), p.y()] for p in v]
                    for k, v in self.all_routes.items()
                }
                with open(self.routes_file, "w") as f:
                    json.dump(data, f)

                self.route_list_widget.addItem(name)
                self.draw_all_routes_debug()  # Debug-Linien aktualisieren
                print(f"Route {name} gespeichert.")

        elif self.is_placing_shelves:
            self.save_shelves()
            print("Regale gespeichert.")

        self.cancel_admin_action()

    def handle_scene_click(self, pos):
        if self.is_drawing_mode:
            self.current_route_points.append(pos)
            dot = self.sim_scene.addEllipse(
                pos.x() - 4,
                pos.y() - 4,
                8,
                8,
                QPen(COLOR_DARK_TEXT),
                QBrush(COLOR_ORANGE),
            )
            dot.setZValue(10)
            self.current_route_point_items.append(dot)

            if len(self.current_route_points) > 1:
                path = QPainterPath()
                path.moveTo(self.current_route_points[0])
                for p in self.current_route_points[1:]:
                    path.lineTo(p)
                self.current_route_path_item.setPath(path)

        elif self.is_placing_shelves:
            self.all_shelves.append(pos)
            shelf = ShelfItem(pos.x(), pos.y())
            # Immer sichtbar während Platzierung
            shelf.setVisible(True)
            self.sim_scene.addItem(shelf)
            self.shelf_items.append(shelf)

    # --- SIMULATION LOGIK ---

    def toggle_simulation(self):
        if self.sim_timer.isActive():
            self.stop_simulation()
        else:
            self.start_simulation()

    def start_simulation(self):
        if not self.all_routes:
            print("Keine Routen vorhanden!")
            return

        count = self.actor_count_input.value()
        route_names = list(self.all_routes.keys())

        self.clear_customers()
        self.queue_count = 0
        self.lbl_queue_count.setText("0")

        for _ in range(count):
            r_name = random.choice(route_names)
            route = self.all_routes[r_name]
            customer = CustomerItem(route, self.all_shelves)
            self.sim_scene.addItem(customer)
            self.customers.append(customer)

        self.start_sim_button.setText("Simulation stoppen")
        self.sim_timer.start(SIM_TICK_MS)

    def stop_simulation(self):
        self.sim_timer.stop()
        self.start_sim_button.setText("Simulation starten")

    def clear_customers(self):
        for c in self.customers:
            self.sim_scene.removeItem(c)
        self.customers.clear()

    def simulation_tick(self):
        active_customers = []
        for customer in self.customers:
            customer.tick()

            if customer.state == "FINISHED":
                self.queue_count += 1
                self.lbl_queue_count.setText(str(self.queue_count))
                self.sim_scene.removeItem(customer)
            else:
                active_customers.append(customer)

        self.customers = active_customers

        if not self.customers:
            self.stop_simulation()

    # --- Helpers ---
    def delete_selected_route(self):
        sel = self.route_list_widget.selectedItems()
        if not sel:
            return
        item = sel[0]
        name = item.text()
        del self.all_routes[name]
        self.route_list_widget.takeItem(self.route_list_widget.row(item))

        data = {
            k: [[p.x(), p.y()] for p in v] for k, v in self.all_routes.items()
        }
        with open(self.routes_file, "w") as f:
            json.dump(data, f)

        self.draw_all_routes_debug()  # Update Debug

    def show_route_details(self, item):
        # Vereinfacht: Nur anzeigen, wenn Debug an ist oder im Canvas malen
        pass

    def toggle_simulation_fullscreen(self):
        if self.is_q1_maximized:
            self.toggle_q1_fullscreen()
            return
        if self.is_admin_mode:
            return
        self.is_sim_maximized = not self.is_sim_maximized
        if self.is_sim_maximized:
            self.top_row_widget.hide()
            self.bottom_right_group_box.hide()
            self.minimize_sim_button.show()
            self.bottom_left_group_box.setTitle("Live-Simulation (Vollbild)")
            if self.item_q1:
                self.item_q1.setEnabled(False)
        else:
            self.top_row_widget.show()
            self.bottom_right_group_box.show()
            self.minimize_sim_button.hide()
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            if self.item_q1:
                self.item_q1.setEnabled(True)
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

    def toggle_q1_fullscreen(self):
        if not self.item_q1 or self.is_admin_mode:
            return
        self.is_q1_maximized = not self.is_q1_maximized
        if self.is_q1_maximized:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.hide()
            self.minimize_q1_button.show()
            self.sim_view.fitInView(
                self.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
            self.bottom_left_group_box.setTitle("Kassenbereich (Vollbild)")
            if self.is_sim_maximized:
                self.minimize_sim_button.hide()
        else:
            for i in [self.item_q2, self.item_q3, self.item_q4]:
                i.show()
            self.minimize_q1_button.hide()
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )
            if self.is_sim_maximized:
                self.minimize_sim_button.show()
                self.bottom_left_group_box.setTitle(
                    "Live-Simulation (Vollbild)"
                )
            else:
                self.bottom_left_group_box.setTitle(
                    "Live-Simulation (Miniatur)"
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
