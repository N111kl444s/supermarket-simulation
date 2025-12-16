import sys
import json
import random
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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
)

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QObject, QPointF, QTimer
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QColor,
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
COLOR_SHELF = QColor("#3F51B5")
COLOR_CUSTOMER = QColor("#E91E63")
COLOR_CASHIER = QColor("#FFD700")
COLOR_CHECKOUT = QColor("#607D8B")
COLOR_WAITING_AREA = QColor(0, 255, 0, 30)

# --- KONSTANTEN ---
SHELF_SIZE = 20
CUSTOMER_SIZE = 12
CASHIER_SIZE = 14
CHECKOUT_WIDTH = 40
CHECKOUT_HEIGHT = 30
SIM_TICK_MS = 30
SHELF_PROBABILITY = 0.3
WALK_SPEED = 3.0

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
        self.setMouseTracking(True)

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


# --- VISUELLE ITEMS ---


class WaitingAreaItem(QGraphicsRectItem):
    def __init__(self, rect: QRectF):
        super().__init__(rect)
        self.setBrush(QBrush(COLOR_WAITING_AREA))
        self.setPen(QPen(COLOR_GREEN, 2, Qt.PenStyle.DashLine))
        self.setZValue(2)


class CheckoutItem(QGraphicsObject):
    """
    Stellt eine Kasse dar.
    orientation: 'Left' oder 'Right' (Bestimmt Seite von Kassierer/Schlange)
    """

    def __init__(
        self, x, y, c_type="Normal", orientation="Right", is_open=True
    ):
        super().__init__()
        self.setPos(x, y)
        self.c_type = c_type
        self.orientation = orientation
        self.is_open = is_open
        self.setZValue(6)

    def boundingRect(self):
        return QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

    def paint(self, painter: QPainter, option, widget=None):
        # Kassenkörper
        painter.setBrush(QBrush(COLOR_CHECKOUT))
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawRect(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT)

        # Orientierungs-Indikator (Streifen an der Seite)
        painter.setBrush(QBrush(Qt.GlobalColor.darkGray))
        painter.setPen(Qt.PenStyle.NoPen)
        if self.orientation == "Left":
            painter.drawRect(0, 0, 5, CHECKOUT_HEIGHT)  # Streifen Links
        else:
            painter.drawRect(
                CHECKOUT_WIDTH - 5, 0, 5, CHECKOUT_HEIGHT
            )  # Streifen Rechts

        # Text
        painter.setPen(Qt.GlobalColor.white)
        label = "SB" if self.c_type == "SB" else "K"
        painter.drawText(
            QRectF(0, 0, CHECKOUT_WIDTH, CHECKOUT_HEIGHT),
            Qt.AlignmentFlag.AlignCenter,
            label,
        )

        # Status Licht (Oben mittig)
        status_color = (
            Qt.GlobalColor.green if self.is_open else Qt.GlobalColor.red
        )
        painter.setBrush(QBrush(status_color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(int(CHECKOUT_WIDTH / 2) - 4, 2, 8, 8)


class CashierItem(QGraphicsEllipseItem):
    def __init__(self, x, y, skill="Azubi"):
        super().__init__(0, 0, CASHIER_SIZE, CASHIER_SIZE)
        self.setPos(x, y)
        self.setBrush(QBrush(COLOR_CASHIER))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(25)
        self.skill = skill
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setToolTip(f"Kassierer ({self.skill})")
        super().hoverEnterEvent(event)


class ShelfItem(QGraphicsRectItem):
    def __init__(self, x, y):
        super().__init__(
            x - SHELF_SIZE / 2, y - SHELF_SIZE / 2, SHELF_SIZE, SHELF_SIZE
        )
        self.setBrush(QBrush(COLOR_SHELF))
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setZValue(5)
        self.setVisible(False)


class CustomerItem(QGraphicsEllipseItem):
    def __init__(self, route_points, all_shelves_pos, waiting_area_rect):
        super().__init__(
            -CUSTOMER_SIZE / 2,
            -CUSTOMER_SIZE / 2,
            CUSTOMER_SIZE,
            CUSTOMER_SIZE,
        )
        self.setBrush(QBrush(COLOR_CUSTOMER))
        self.setPen(QPen(Qt.GlobalColor.white))
        self.setZValue(20)

        self.route = route_points
        self.shelves = all_shelves_pos
        self.waiting_area = waiting_area_rect

        self.current_waypoint_idx = 0
        self.state = "WALKING_ROUTE"
        self.wait_ticks = 0
        self.return_pos = None
        self.target_pos = QPointF(0, 0)

        if self.route:
            self.setPos(self.route[0])
            if len(self.route) > 1:
                self.current_waypoint_idx = 1
                self.target_pos = self.route[1]
            else:
                self.enter_waiting_area()

    def tick(self):
        if self.state == "FINISHED_SHOPPING":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                if self.waiting_area:
                    rx = random.uniform(
                        self.waiting_area.left(), self.waiting_area.right()
                    )
                    ry = random.uniform(
                        self.waiting_area.top(), self.waiting_area.bottom()
                    )
                    self.target_pos = QPointF(rx, ry)
                    self.wait_ticks = random.randint(50, 150)
            self.move_towards_target()
            return

        if self.state == "WAITING_AT_SHELF":
            self.wait_ticks -= 1
            if self.wait_ticks <= 0:
                self.state = "RETURNING_TO_ROUTE"
                self.target_pos = self.return_pos
            return

        self.move_towards_target()

    def move_towards_target(self):
        current_pos = QVector2D(self.pos())
        target = QVector2D(self.target_pos)
        direction = target - current_pos
        distance = direction.length()

        if distance < WALK_SPEED:
            self.setPos(self.target_pos)
            self.handle_target_reached()
        else:
            direction.normalize()
            new_pos = current_pos + direction * WALK_SPEED
            self.setPos(new_pos.toPointF())

    def handle_target_reached(self):
        if self.state == "FINISHED_SHOPPING":
            return

        if self.state == "WALKING_TO_SHELF":
            self.state = "WAITING_AT_SHELF"
            sec = random.uniform(1.0, 3.0)
            self.wait_ticks = int((sec * 1000) / SIM_TICK_MS)

        elif self.state == "RETURNING_TO_ROUTE":
            self.state = "WALKING_ROUTE"
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.route):
                self.enter_waiting_area()
            else:
                self.target_pos = self.route[self.current_waypoint_idx]

        elif self.state == "WALKING_ROUTE":
            if self.current_waypoint_idx < len(self.route) - 1:
                if self.shelves and random.random() < SHELF_PROBABILITY:
                    shelf = self.find_nearest_shelf()
                    if shelf:
                        self.state = "WALKING_TO_SHELF"
                        self.return_pos = self.target_pos
                        self.target_pos = shelf
                        return

            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.route):
                self.enter_waiting_area()
            else:
                self.target_pos = self.route[self.current_waypoint_idx]

    def enter_waiting_area(self):
        self.state = "FINISHED_SHOPPING"
        self.wait_ticks = 0
        if not self.waiting_area:
            self.target_pos = self.pos()

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
    waiting_area_created = pyqtSignal(QRectF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = None
        self.rect_start_point = None
        self.temp_rect_item = None

    def mousePressEvent(self, event):
        if self.main_window and self.main_window.is_admin_mode:
            if self.main_window.is_drawing_waiting_area:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.rect_start_point = event.scenePos()
                    self.temp_rect_item = QGraphicsRectItem()
                    self.temp_rect_item.setPen(
                        QPen(COLOR_GREEN, 2, Qt.PenStyle.DashLine)
                    )
                    self.addItem(self.temp_rect_item)
                    event.accept()
                    return

            if (
                self.main_window.is_drawing_mode
                or self.main_window.is_placing_shelves
                or self.main_window.is_placing_checkout
            ):
                if event.button() == Qt.MouseButton.LeftButton:
                    pos = event.scenePos()
                    if self.sceneRect().contains(pos):
                        self.clicked_point.emit(pos)
                        event.accept()
                        return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (
            self.main_window.is_drawing_waiting_area
            and self.rect_start_point
            and self.temp_rect_item
        ):
            current_pos = event.scenePos()
            rect = QRectF(self.rect_start_point, current_pos).normalized()
            self.temp_rect_item.setRect(rect)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.main_window.is_drawing_waiting_area and self.rect_start_point:
            if event.button() == Qt.MouseButton.LeftButton:
                current_pos = event.scenePos()
                rect = QRectF(self.rect_start_point, current_pos).normalized()
                self.removeItem(self.temp_rect_item)
                self.temp_rect_item = None
                self.rect_start_point = None
                self.waiting_area_created.emit(rect)
                event.accept()
                return
        super().mouseReleaseEvent(event)


# --- MAIN WINDOW ---


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Prototyp 8: Richtungs-Kassen & Persistenz (Projekt: Piep)"
        )
        self.setGeometry(100, 100, 1400, 900)

        self.is_sim_maximized = False
        self.is_q1_maximized = False
        self.is_admin_mode = False
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_placing_checkout = False

        # Kassen-Platzierung Status
        self.current_checkout_type = "Normal"
        self.current_checkout_orientation = "Right"  # "Left" or "Right"

        self.show_debug_overlays = False

        self.routes_file = BASE_DIR / "routes.json"
        self.shelves_file = BASE_DIR / "shelves.json"
        self.checkouts_file = BASE_DIR / "checkouts.json"
        self.waiting_area_file = BASE_DIR / "waiting_area.json"

        self.all_routes = {}
        self.all_shelves = []
        self.checkouts_data = []  # {x, y, type, id, skill, open, orientation}
        self.waiting_area_rect = None

        self.current_route_points = []

        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulation_tick)
        self.customers = []
        self.cashier_items = []
        self.queue_count = 0

        self.item_q1 = None
        self.item_q2 = None
        self.item_q3 = None
        self.item_q4 = None
        self.current_route_path_item = None
        self.current_route_point_items = []
        self.shelf_items = []
        self.checkout_items = []
        self.waiting_area_item = None
        self.route_debug_items = (
            []
        )  # Debug Linien für Routen UND Warteschlangen
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
        sim_layout = QVBoxLayout(sim_widget)
        form_layout = QFormLayout()

        self.sim_name_input = QLineEdit("Simulation_01")
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(10)
        self.actor_count_input.setRange(1, 200)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 500)
        self.speed_slider.setValue(150)

        form_layout.addRow("Name:", self.sim_name_input)
        form_layout.addRow("Kunden:", self.actor_count_input)
        form_layout.addRow("Tempo:", self.speed_slider)
        sim_layout.addLayout(form_layout)

        sim_layout.addWidget(QLabel("Kassen-Verwaltung:"))
        self.checkout_table = QTableWidget()
        self.checkout_table.setColumnCount(4)
        self.checkout_table.setHorizontalHeaderLabels(
            ["ID", "Typ/Ort", "Status", "Skill"]
        )
        self.checkout_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.checkout_table.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        sim_layout.addWidget(self.checkout_table)

        self.start_sim_button = QPushButton("Simulation starten")
        self.start_sim_button.setObjectName("StartButton")
        self.start_sim_button.clicked.connect(self.toggle_simulation)
        sim_layout.addWidget(self.start_sim_button)

        # --- Admin Widget ---
        admin_widget = QWidget()
        admin_layout = QVBoxLayout(admin_widget)

        self.chk_show_debug = QCheckBox("Elemente & Routen anzeigen")
        self.chk_show_debug.toggled.connect(self.toggle_debug_view)

        self.new_route_button = QPushButton("Neue Route zeichnen")
        self.new_route_button.clicked.connect(self.start_drawing_mode)

        self.place_shelves_button = QPushButton("Regale platzieren")
        self.place_shelves_button.clicked.connect(self.start_shelf_mode)

        self.waiting_area_button = QPushButton("Wartebereich setzen")
        self.waiting_area_button.clicked.connect(self.start_waiting_area_mode)

        # Kassen Platzierung (4 Buttons)
        checkout_layout = QFormLayout()

        btn_norm_l = QPushButton("Normal (Links)")
        btn_norm_l.clicked.connect(
            lambda: self.start_checkout_mode("Normal", "Left")
        )
        btn_norm_r = QPushButton("Normal (Rechts)")
        btn_norm_r.clicked.connect(
            lambda: self.start_checkout_mode("Normal", "Right")
        )

        btn_sb_l = QPushButton("SB (Links)")
        btn_sb_l.clicked.connect(
            lambda: self.start_checkout_mode("SB", "Left")
        )
        btn_sb_r = QPushButton("SB (Rechts)")
        btn_sb_r.clicked.connect(
            lambda: self.start_checkout_mode("SB", "Right")
        )

        checkout_layout.addRow(QLabel("Kassen platzieren:"))
        checkout_layout.addRow(btn_norm_l, btn_norm_r)
        checkout_layout.addRow(btn_sb_l, btn_sb_r)

        admin_layout.addWidget(self.chk_show_debug)
        admin_layout.addWidget(self.new_route_button)
        admin_layout.addWidget(self.place_shelves_button)
        admin_layout.addWidget(self.waiting_area_button)
        admin_layout.addLayout(checkout_layout)
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
        values_layout.addRow("Kunden im Wartebereich:", self.lbl_queue_count)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
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

        self.admin_toolbar = QWidget()
        tb_layout = QHBoxLayout(self.admin_toolbar)
        self.btn_admin_save = QPushButton("Speichern")
        self.btn_admin_save.clicked.connect(self.finish_admin_action)
        self.btn_admin_cancel = QPushButton("Abbrechen")
        self.btn_admin_cancel.clicked.connect(self.cancel_admin_action)
        tb_layout.addWidget(self.btn_admin_save)
        tb_layout.addWidget(self.btn_admin_cancel)
        layout.addWidget(self.admin_toolbar)
        self.admin_toolbar.hide()

        self.sim_scene = RouteEditorScene(self)
        self.sim_scene.main_window = self
        self.sim_scene.clicked_point.connect(self.handle_scene_click)
        self.sim_scene.waiting_area_created.connect(
            self.handle_waiting_area_created
        )
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))

        self.sim_view = AutoFitGraphicsView(self.sim_scene)
        layout.addWidget(self.sim_view)

        try:
            path_q1 = str(IMAGE_DIR / "quadrant_1.png")
            path_q2 = str(IMAGE_DIR / "quadrant_2.png")
            path_q3 = str(IMAGE_DIR / "quadrant_3.png")
            path_q4 = str(IMAGE_DIR / "quadrant_4.png")
            self.item_q1 = ClickablePixmapItem(QPixmap(path_q1))
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(self.toggle_q1_fullscreen)

            self.item_q2 = self.sim_scene.addPixmap(QPixmap(path_q2))
            self.item_q2.setPos(800, 0)
            self.item_q3 = self.sim_scene.addPixmap(QPixmap(path_q3))
            self.item_q3.setPos(0, 450)
            self.item_q4 = self.sim_scene.addPixmap(QPixmap(path_q4))
            self.item_q4.setPos(800, 450)

            self.scene_rect = QRectF(0, 0, 1600, 900)
            self.sim_scene.setSceneRect(self.scene_rect)
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )
        except:
            pass

        return group_box

    def create_bottom_right_quadrant(self):
        group_box = QGroupBox("Zukünftige Anforderungen")
        self.bottom_right_stack = QStackedWidget(group_box)
        layout = QVBoxLayout(group_box)
        layout.addWidget(self.bottom_right_stack)
        txt = QTextEdit("Platzhalter...")
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

    # --- DATEN MANAGEMENT ---

    def load_data(self):
        # Routen
        if self.routes_file.exists():
            try:
                with open(self.routes_file, "r") as f:
                    data = json.load(f)
                    self.all_routes = {
                        k: [QPointF(p[0], p[1]) for p in v]
                        for k, v in data.items()
                    }
                for name in self.all_routes:
                    self.route_list_widget.addItem(name)
            except:
                pass

        # Regale
        if self.shelves_file.exists():
            try:
                with open(self.shelves_file, "r") as f:
                    data = json.load(f)
                    self.all_shelves = [QPointF(p[0], p[1]) for p in data]
            except:
                pass

        # Wartebereich
        if self.waiting_area_file.exists():
            try:
                with open(self.waiting_area_file, "r") as f:
                    rect_list = json.load(f)
                    self.waiting_area_rect = QRectF(*rect_list)
                    self.draw_waiting_area()
            except:
                pass

        # Kassen
        if self.checkouts_file.exists():
            try:
                with open(self.checkouts_file, "r") as f:
                    self.checkouts_data = json.load(f)
            except:
                pass

        # Alles laden
        self.update_checkout_table()
        # Initialer Debug Draw State (abhängig von toggle)
        self.draw_debug_elements()

    def save_data_generic(self, file_path, data):
        with open(file_path, "w") as f:
            json.dump(data, f)

    def draw_waiting_area(self):
        if self.waiting_area_item:
            self.sim_scene.removeItem(self.waiting_area_item)
        if self.waiting_area_rect:
            self.waiting_area_item = WaitingAreaItem(self.waiting_area_rect)
            self.sim_scene.addItem(self.waiting_area_item)

    def draw_debug_elements(self):
        """Zeichnet/Aktualisiert Regale, Kassen und Debug-Linien basierend auf show_debug_overlays."""
        is_visible = (
            self.show_debug_overlays
            or self.is_placing_shelves
            or self.is_drawing_mode
        )

        # 1. Regale
        for item in self.shelf_items:
            self.sim_scene.removeItem(item)
        self.shelf_items.clear()
        for pos in self.all_shelves:
            shelf = ShelfItem(pos.x(), pos.y())
            shelf.setVisible(is_visible)
            self.sim_scene.addItem(shelf)
            self.shelf_items.append(shelf)

        # 2. Kassen & Warteschlangen-Linien
        for item in self.checkout_items:
            self.sim_scene.removeItem(item)
        for item in self.route_debug_items:
            self.sim_scene.removeItem(item)
        self.checkout_items.clear()
        self.route_debug_items.clear()

        line_pen = QPen(QColor(200, 0, 0, 100), 2, Qt.PenStyle.DashLine)
        route_pen = QPen(QColor(100, 100, 100, 100), 2, Qt.PenStyle.DotLine)

        # Kassen
        for c_data in self.checkouts_data:
            # Kasse ist immer sichtbar, nicht nur im Debug
            item = CheckoutItem(
                c_data["x"],
                c_data["y"],
                c_data["type"],
                c_data.get("orientation", "Right"),
                c_data["open"],
            )
            self.sim_scene.addItem(item)
            self.checkout_items.append(item)

            # Warteschlange (Debug Linie)
            orientation = c_data.get("orientation", "Right")
            start_x = c_data["x"] + (
                5 if orientation == "Left" else CHECKOUT_WIDTH - 5
            )
            start_y = c_data["y"] + CHECKOUT_HEIGHT
            end_x = start_x
            end_y = start_y + 60  # Schlange geht nach unten

            if self.show_debug_overlays:
                pp = QPainterPath()
                pp.moveTo(start_x, start_y)
                pp.lineTo(end_x, end_y)
                line = QGraphicsPathItem(pp)
                line.setPen(line_pen)
                self.sim_scene.addItem(line)
                self.route_debug_items.append(line)

        # Routen (nur wenn Debug an)
        if self.show_debug_overlays:
            for name, points in self.all_routes.items():
                if len(points) > 1:
                    path = QPainterPath()
                    path.moveTo(points[0])
                    for p in points[1:]:
                        path.lineTo(p)
                    pi = QGraphicsPathItem(path)
                    pi.setPen(route_pen)
                    pi.setZValue(4)
                    self.sim_scene.addItem(pi)
                    self.route_debug_items.append(pi)

    def update_checkout_table(self):
        self.checkout_table.setRowCount(len(self.checkouts_data))
        for i, c_data in enumerate(self.checkouts_data):
            self.checkout_table.setItem(
                i, 0, QTableWidgetItem(str(c_data.get("id", i + 1)))
            )

            # Typ & Orientierung
            ori = c_data.get("orientation", "R")
            typ_str = f"{c_data['type']} ({ori})"
            self.checkout_table.setItem(i, 1, QTableWidgetItem(typ_str))

            chk_open = QCheckBox()
            chk_open.setChecked(c_data["open"])
            chk_open.toggled.connect(
                lambda checked, idx=i: self.on_checkout_status_changed(
                    idx, checked
                )
            )
            w_status = QWidget()
            l = QHBoxLayout(w_status)
            l.addWidget(chk_open)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)
            self.checkout_table.setCellWidget(i, 2, w_status)

            if c_data["type"] == "Normal":
                combo = QComboBox()
                combo.addItems(["Azubi", "Erfahren", "Profi"])
                combo.setCurrentText(c_data.get("skill", "Azubi"))
                combo.currentTextChanged.connect(
                    lambda text, idx=i: self.on_checkout_skill_changed(
                        idx, text
                    )
                )
                self.checkout_table.setCellWidget(i, 3, combo)
            else:
                self.checkout_table.setItem(i, 3, QTableWidgetItem("-"))

    def on_checkout_status_changed(self, idx, is_open):
        self.checkouts_data[idx]["open"] = is_open
        self.save_data_generic(self.checkouts_file, self.checkouts_data)
        self.draw_debug_elements()  # Re-Draw für Status-Licht update

    def on_checkout_skill_changed(self, idx, skill):
        self.checkouts_data[idx]["skill"] = skill
        self.save_data_generic(self.checkouts_file, self.checkouts_data)

    def toggle_debug_view(self, checked):
        self.show_debug_overlays = checked
        self.draw_debug_elements()

    # --- ADMIN ACTIONS ---

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
            # WICHTIG: Debug View Status bleibt erhalten!

    def start_drawing_mode(self):
        self.is_drawing_mode = True
        self.setup_admin_fullscreen("Route zeichnen")
        self.current_route_points = []
        pen = QPen(COLOR_ORANGE, 3, Qt.PenStyle.DashLine)
        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(pen)
        self.sim_scene.addItem(self.current_route_path_item)

    def start_shelf_mode(self):
        self.is_placing_shelves = True
        self.setup_admin_fullscreen("Regale platzieren")
        self.draw_debug_elements()  # Force visible

    def start_waiting_area_mode(self):
        self.is_drawing_waiting_area = True
        self.setup_admin_fullscreen("Wartebereich ziehen (Drag & Drop)")
        if self.waiting_area_item:
            self.waiting_area_item.setVisible(True)

    def start_checkout_mode(self, c_type, orientation):
        self.is_placing_checkout = True
        self.current_checkout_type = c_type
        self.current_checkout_orientation = orientation
        self.setup_admin_fullscreen(f"Kasse ({c_type} - {orientation})")

    def setup_admin_fullscreen(self, title):
        self.top_row_widget.hide()
        self.bottom_right_group_box.hide()
        self.admin_toolbar.show()
        self.bottom_left_group_box.setTitle(f"Editor: {title}")
        self.bottom_left_group_box.setEnabled(True)

    def cancel_admin_action(self):
        self.is_drawing_mode = False
        self.is_placing_shelves = False
        self.is_drawing_waiting_area = False
        self.is_placing_checkout = False

        if self.current_route_path_item:
            self.sim_scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None
        for item in self.current_route_point_items:
            self.sim_scene.removeItem(item)
        self.current_route_point_items.clear()

        self.admin_toolbar.hide()
        self.top_row_widget.show()
        self.bottom_right_group_box.show()
        self.bottom_left_group_box.setTitle("Routen-Editor")
        self.bottom_left_group_box.setEnabled(False)

        self.draw_debug_elements()  # Reset visibility to checkbox state

    def finish_admin_action(self):
        if self.is_drawing_mode and self.current_route_points:
            name = f"Route_{len(self.all_routes) + 1}"
            self.all_routes[name] = list(self.current_route_points)
            data = {
                k: [[p.x(), p.y()] for p in v]
                for k, v in self.all_routes.items()
            }
            self.save_data_generic(self.routes_file, data)
            self.route_list_widget.addItem(name)
        elif self.is_placing_shelves:
            data = [[p.x(), p.y()] for p in self.all_shelves]
            self.save_data_generic(self.shelves_file, data)
        elif self.is_drawing_waiting_area and self.waiting_area_rect:
            data = [
                self.waiting_area_rect.x(),
                self.waiting_area_rect.y(),
                self.waiting_area_rect.width(),
                self.waiting_area_rect.height(),
            ]
            self.save_data_generic(self.waiting_area_file, data)

        # Kassen speichern automatisch bei Klick, aber hier Refreh schadet nicht
        self.draw_debug_elements()
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
            # Temporär zeichnen
            shelf = ShelfItem(pos.x(), pos.y())
            shelf.setVisible(True)
            self.sim_scene.addItem(shelf)
            self.shelf_items.append(shelf)

        elif self.is_placing_checkout:
            new_id = len(self.checkouts_data) + 1
            new_checkout = {
                "id": new_id,
                "x": pos.x(),
                "y": pos.y(),
                "type": self.current_checkout_type,
                "orientation": self.current_checkout_orientation,
                "open": True,
                "skill": (
                    "Azubi" if self.current_checkout_type == "Normal" else None
                ),
            }
            self.checkouts_data.append(new_checkout)
            self.save_data_generic(self.checkouts_file, self.checkouts_data)
            self.draw_debug_elements()
            self.update_checkout_table()

    def handle_waiting_area_created(self, rect):
        self.waiting_area_rect = rect
        self.draw_waiting_area()

    # --- SIMULATION LOGIK ---

    def start_simulation(self):
        if not self.all_routes:
            return
        count = self.actor_count_input.value()
        route_names = list(self.all_routes.keys())
        self.clear_customers()
        self.queue_count = 0
        self.lbl_queue_count.setText("0")

        # Kassierer platzieren
        for item in self.cashier_items:
            self.sim_scene.removeItem(item)
        self.cashier_items.clear()

        for c_data in self.checkouts_data:
            if c_data["type"] == "Normal":
                cx, cy = c_data["x"], c_data["y"]
                ori = c_data.get("orientation", "Right")

                # Positionierung basierend auf Orientierung
                # Kasse: 40x30.
                # Right: Kassierer rechts (x+40), mittig (y+15)
                # Left: Kassierer links (x-CashierSize), mittig
                if ori == "Left":
                    c_pos_x = cx - CASHIER_SIZE
                else:
                    c_pos_x = cx + CHECKOUT_WIDTH

                c_pos_y = cy + (CHECKOUT_HEIGHT / 2) - (CASHIER_SIZE / 2)

                cashier = CashierItem(
                    c_pos_x, c_pos_y, c_data.get("skill", "Azubi")
                )
                self.sim_scene.addItem(cashier)
                self.cashier_items.append(cashier)

        for _ in range(count):
            r_name = random.choice(route_names)
            customer = CustomerItem(
                self.all_routes[r_name],
                self.all_shelves,
                self.waiting_area_rect,
            )
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
        waiting_count = 0
        for customer in self.customers:
            customer.tick()
            if customer.state == "FINISHED_SHOPPING":
                waiting_count += 1
            active_customers.append(customer)

        self.customers = active_customers
        self.lbl_queue_count.setText(str(waiting_count))

    # --- Helper ---

    def toggle_simulation(self):
        if self.sim_timer.isActive():
            self.stop_simulation()
        else:
            self.start_simulation()

    def delete_selected_route(self):
        sel = self.route_list_widget.selectedItems()
        if not sel:
            return
        name = sel[0].text()
        del self.all_routes[name]
        self.route_list_widget.takeItem(self.route_list_widget.row(sel[0]))
        data = {
            k: [[p.x(), p.y()] for p in v] for k, v in self.all_routes.items()
        }
        self.save_data_generic(self.routes_file, data)
        self.draw_debug_elements()

    def show_route_details(self, item):
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
