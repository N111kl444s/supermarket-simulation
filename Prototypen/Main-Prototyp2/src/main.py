import sys
import json  # Für JSON-Speicherung
from pathlib import Path  # Für dynamische Pfade
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
    QGraphicsPixmapItem,
    QGraphicsObject,  # Für klickbare Items mit Signalen
    # Imports für Admin-Modus
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QGraphicsPathItem,
)

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QObject, QPointF
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPixmap,
    QPainterPath,
)

import pyqtgraph as pg

# --- Dynamische Pfad-Erstellung ---
SCRIPT_FILE = Path(__file__).resolve()
SRC_DIR = SCRIPT_FILE.parent
BASE_DIR = SRC_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"


# --- Projekt: Piep Farbpalette (basierend auf Logo) ---
COLOR_ORANGE = QColor("#FF6A00")
COLOR_TURQUOISE = QColor("#00B0D0")
COLOR_GREEN = QColor("#50C878")
COLOR_DARK_TEXT = QColor("#333333")
COLOR_MEDIUM_TEXT = QColor("#666666")
COLOR_LIGHT_BG = QColor("#F8F8F8")
COLOR_WHITE_BG = QColor("#FFFFFF")
COLOR_BORDER = QColor("#E0E0E0")


# --- KLASSE: ClickableGroupBox ---
class ClickableGroupBox(QGroupBox):
    """
    Eine QGroupBox, die ein 'clicked'-Signal aussendet,
    wenn man mit der linken Maustaste darauf klickt.
    Wird für den KARTEN-Zoom verwendet.
    """

    clicked = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# --- KLASSE: ClickablePixmapItem ---
class ClickablePixmapItem(QGraphicsObject):
    """
    Ein klickbares Pixmap-Item.
    Erbt von QGraphicsObject, um Signale (QObject) und
    Grafik-Item-Eigenschaften (QGraphicsItem) zu kombinieren.
    """

    clicked = pyqtSignal()

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap

    def boundingRect(self):
        """Gibt die Bounding Box des Items zurück (Größe des Bildes)."""
        return QRectF(self.pixmap.rect())

    def paint(self, painter: QPainter, option, widget=None):
        """Zeichnet das Pixmap."""
        painter.drawPixmap(0, 0, self.pixmap)

    def mousePressEvent(self, event):
        """Überschreibt das Maus-Klick-Event für das Item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()  # Stoppt das Event hier
        else:
            super().mousePressEvent(event)


# --- KLASSE: RouteEditorScene ---
class RouteEditorScene(QGraphicsScene):
    """
    Eine Szene, die Mausklicks abfängt, um Routenpunkte zu zeichnen,
    wenn sich die Anwendung im 'is_drawing_mode' befindet.
    """

    # Signal, das die Klick-Position an die MainWindow sendet
    waypoint_clicked = pyqtSignal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Zugriff auf die MainWindow (wird beim Erstellen gesetzt)
        self.main_window = None

    def mousePressEvent(self, event):
        """Wird bei JEDEM Klick in die Szene aufgerufen."""
        if not self.main_window:
            super().mousePressEvent(event)
            return

        # Nur reagieren, wenn wir im Admin- UND Zeichenmodus sind
        if self.main_window.is_admin_mode and self.main_window.is_drawing_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.scenePos()  # Die 1600x900-Koordinate

                if self.sceneRect().contains(pos):
                    # Signal an MainWindow senden, um Punkt zu verarbeiten
                    self.waypoint_clicked.emit(pos)
                    event.accept()
                    return

        # Events weiterleiten, wenn wir NICHT zeichnen
        super().mousePressEvent(event)


# --- KLASSE: AutoFitGraphicsView ---
class AutoFitGraphicsView(QGraphicsView):
    """
    Eine QGraphicsView, die ihren Inhalt (die Szene) automatisch
    an ihre eigene Größe anpasst und das Seitenverhältnis beibehält,
    ohne Scrollbalken anzuzeigen.
    """

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        """Passt die Ansicht bei Größenänderung an."""
        super().resizeEvent(event)

        if self.scene() and not self.sceneRect().isEmpty():
            main_window = self.window()
            if (
                main_window
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


# --- 1. Das Hauptfenster ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Prototyp 6.2: Echter Vollbild-Editor (Projekt: Piep)"
        )
        self.setGeometry(100, 100, 1400, 900)

        # === Zoom-Zustände ===
        self.is_sim_maximized = False
        self.is_q1_maximized = False

        # === Admin-Zustände ===
        self.is_admin_mode = False
        self.is_drawing_mode = False

        # === Daten-Speicher ===
        self.routes_file = BASE_DIR / "routes.json"
        self.all_routes = {}  # Dict: {"Routenname": [QPointF, ...]}
        self.current_route_points = []  # Temp-Liste für aktuelle Zeichnung

        # === Item-Referenzen ===
        self.item_q1 = None
        self.item_q2 = None
        self.item_q3 = None
        self.item_q4 = None
        self.current_route_path_item = None
        self.current_route_point_items = []
        self.scene_rect = QRectF()

        self.top_left_group_box = None
        self.top_right_group_box = None
        self.bottom_left_group_box = None
        self.bottom_right_group_box = None

        self.setup_ui()

        self.load_routes_from_json()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Obere Reihe (als QWidget) ---
        self.top_row_widget = QWidget()
        top_row_layout = QHBoxLayout(self.top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(10)

        self.top_left_group_box = self.create_top_left_quadrant()
        self.top_right_group_box = self.create_top_right_quadrant()
        top_row_layout.addWidget(self.top_left_group_box, 1)
        top_row_layout.addWidget(self.top_right_group_box, 1)

        # --- Untere Reihe (als QWidget) ---
        self.bottom_row_widget = QWidget()
        bottom_row_layout = QHBoxLayout(self.bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(10)

        self.bottom_left_group_box = self.create_bottom_left_quadrant()
        self.bottom_right_group_box = self.create_bottom_right_quadrant()
        bottom_row_layout.addWidget(self.bottom_left_group_box, 1)
        bottom_row_layout.addWidget(self.bottom_right_group_box, 1)

        # Reihen zum Hauptlayout hinzufügen
        main_layout.addWidget(self.top_row_widget, 1)
        main_layout.addWidget(self.bottom_row_widget, 1)

    # --- Quadranten-Erstellungs-Methoden ---

    def create_top_left_quadrant(self):
        """
        Erstellt den Quadranten Oben-Links.
        Enthält die (immer sichtbare) Admin-Checkbox und ein StackedWidget
        für Sim-Settings ODER Routen-Verwaltung.
        """
        group_box = QGroupBox("Eingabeparameter")

        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Admin-Checkbox (immer sichtbar)
        self.admin_mode_checkbox = QCheckBox("Admin-Modus")
        self.admin_mode_checkbox.toggled.connect(self.toggle_admin_mode)
        layout.addWidget(self.admin_mode_checkbox)

        # Stacked Widget für den Rest
        self.top_left_stack = QStackedWidget()
        layout.addWidget(self.top_left_stack)

        # --- Index 0: Simulationseinstellungen ---
        sim_widget = QWidget()
        sim_layout = QFormLayout(sim_widget)
        sim_layout.setSpacing(10)

        self.sim_name_input = QLineEdit("Simulation_01")
        self.actor_count_input = QSpinBox()
        self.actor_count_input.setValue(1)
        self.actor_count_input.setMinimum(1)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 500)
        self.speed_slider.setValue(150)
        self.sim_mode_combo = QComboBox()
        self.sim_mode_combo.addItems(["Modus A", "Modus B", "Modus C"])
        self.logging_checkbox = QCheckBox("Logging aktivieren")
        self.logging_checkbox.setChecked(True)
        self.start_sim_button = QPushButton("Simulation starten")
        self.start_sim_button.setObjectName("StartButton")

        sim_layout.addRow(QLabel("Simulations-Name:"), self.sim_name_input)
        sim_layout.addRow(QLabel("Aktor-Anzahl:"), self.actor_count_input)
        sim_layout.addRow(QLabel("Geschwindigkeit:"), self.speed_slider)
        sim_layout.addRow(QLabel("Simulations-Modus:"), self.sim_mode_combo)
        sim_layout.addRow(self.logging_checkbox)
        sim_layout.addRow(self.start_sim_button)

        # --- Index 1: Routen-Admin-Widget ---
        admin_widget = QWidget()
        admin_layout = QVBoxLayout(admin_widget)

        self.new_route_button = QPushButton("Neue Route zeichnen")
        self.new_route_button.clicked.connect(self.start_drawing_mode)

        admin_layout.addWidget(self.new_route_button)
        admin_layout.addStretch()

        # --- Widgets zum Stack hinzufügen ---
        self.top_left_stack.addWidget(sim_widget)  # Index 0
        self.top_left_stack.addWidget(admin_widget)  # Index 1

        return group_box

    def create_top_right_quadrant(self):
        # (Unverändert)
        group_box = QGroupBox("Ausgabe & Analyse")
        layout = QVBoxLayout(group_box)
        values_layout = QFormLayout()
        values_layout.addRow(QLabel("Gesamtlaufzeit:"), QLabel("0.00 s"))
        values_layout.addRow(QLabel("Aktoren im Ziel:"), QLabel("0 / 0"))
        values_layout.addRow(QLabel("Durchschnittszeit:"), QLabel("N/A"))
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)
        self.plot_widget.setTitle(
            "Ergebnisse (Live)", color=COLOR_DARK_TEXT.name()
        )
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.plot(
            [0, 1, 2, 3, 4],
            [0, 5, 10, 8, 12],
            pen=pg.mkPen(color=COLOR_GREEN, width=2),
        )
        layout.addLayout(values_layout)
        layout.addWidget(self.plot_widget)
        return group_box

    def create_bottom_left_quadrant(self):
        """
        Erstellt den Quadranten Unten-Links.
        Enthält jetzt die (versteckten) Admin-Knöpfe.
        """

        group_box = ClickableGroupBox("Live-Simulation (Miniatur)")
        group_box.clicked.connect(self.toggle_simulation_fullscreen)
        layout = QVBoxLayout(group_box)

        # Button für KARTEN-Zoom
        self.minimize_sim_button = QPushButton(
            "Zurück zur 4-Quadranten-Ansicht"
        )
        self.minimize_sim_button.setObjectName("MinimizeButton")
        self.minimize_sim_button.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        self.minimize_sim_button.hide()
        layout.addWidget(self.minimize_sim_button)

        # Button für Q1-Zoom
        self.minimize_q1_button = QPushButton("Zurück zur Supermarkt-Ansicht")
        self.minimize_q1_button.setObjectName("MinimizeButton")
        self.minimize_q1_button.clicked.connect(self.toggle_q1_fullscreen)
        self.minimize_q1_button.hide()
        layout.addWidget(self.minimize_q1_button)

        # --- Neue Admin-Button-Leiste ---
        self.admin_button_container = QWidget()
        admin_btn_layout = QHBoxLayout(self.admin_button_container)
        admin_btn_layout.setContentsMargins(0, 5, 0, 5)

        self.admin_save_route_button = QPushButton("Route speichern")
        self.admin_save_route_button.clicked.connect(self.save_drawing_mode)

        self.admin_cancel_route_button = QPushButton("Zeichnen abbrechen")
        self.admin_cancel_route_button.clicked.connect(
            self.cancel_drawing_mode
        )

        admin_btn_layout.addWidget(self.admin_save_route_button)
        admin_btn_layout.addWidget(self.admin_cancel_route_button)

        layout.addWidget(self.admin_button_container)
        self.admin_button_container.hide()
        # --- Ende der neuen Toolbar ---

        # --- Szene und View ---
        self.sim_scene = RouteEditorScene(self)
        self.sim_scene.main_window = self
        self.sim_scene.waypoint_clicked.connect(self.add_waypoint)

        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.sim_view = AutoFitGraphicsView(self.sim_scene)

        layout.addWidget(self.sim_view)  # Füge View *nach* den Buttons hinzu

        # --- 4-Quadranten-Tiling (Kacheln) ---
        try:
            QUAD_WIDTH = 800
            QUAD_HEIGHT = 450

            path_q1 = str(IMAGE_DIR / "quadrant_1.png")
            path_q2 = str(IMAGE_DIR / "quadrant_2.png")
            path_q3 = str(IMAGE_DIR / "quadrant_3.png")
            path_q4 = str(IMAGE_DIR / "quadrant_4.png")

            self.pix_q1 = QPixmap(path_q1)
            self.pix_q2 = QPixmap(path_q2)
            self.pix_q3 = QPixmap(path_q3)
            self.pix_q4 = QPixmap(path_q4)

            self.item_q1 = ClickablePixmapItem(self.pix_q1)
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(self.toggle_q1_fullscreen)

            self.item_q2 = self.sim_scene.addPixmap(self.pix_q2)
            self.item_q2.setPos(QUAD_WIDTH, 0)
            self.item_q3 = self.sim_scene.addPixmap(self.pix_q3)
            self.item_q3.setPos(0, QUAD_HEIGHT)
            self.item_q4 = self.sim_scene.addPixmap(self.pix_q4)
            self.item_q4.setPos(QUAD_WIDTH, QUAD_HEIGHT)

            total_width = QUAD_WIDTH * 2
            total_height = QUAD_HEIGHT * 2
            self.scene_rect = QRectF(0, 0, total_width, total_height)
            self.sim_scene.setSceneRect(self.scene_rect)

            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

        except Exception as e:
            print(f"FEHLER beim Laden der Quadranten-Bilder: {e}")
            text_item = self.sim_scene.addText(
                f"Fehler: 4 Quadranten-Bilder in {IMAGE_DIR} nicht gefunden.\n\nERROR: {e}"
            )
            text_item.setDefaultTextColor(QColor("red"))
            self.sim_scene.setSceneRect(0, 0, 400, 300)

        return group_box

    def create_bottom_right_quadrant(self):
        # (Unverändert)
        group_box = QGroupBox("Zukünftige Anforderungen")

        self.bottom_right_stack = QStackedWidget(group_box)
        layout = QVBoxLayout(group_box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.bottom_right_stack)

        # --- Index 0: Platzhalter ---
        placeholder_widget = QWidget()
        placeholder_layout = QVBoxLayout(placeholder_widget)
        self.placeholder_text_edit = QTextEdit(
            "Hier ist Platz für zukünftige Anforderungen...\n\n"
            "Aktivieren Sie den 'Admin-Modus' (oben links), "
            "um die Routen-Verwaltung zu sehen."
        )
        self.placeholder_text_edit.setReadOnly(True)
        placeholder_layout.addWidget(self.placeholder_text_edit)

        # --- Index 1: Routen-Liste ---
        route_list_widget_container = QWidget()
        route_list_layout = QVBoxLayout(route_list_widget_container)

        self.route_list_widget = QListWidget()
        self.route_list_widget.itemClicked.connect(self.show_route_details)

        self.delete_route_button = QPushButton("Ausgewählte Route löschen")
        self.delete_route_button.clicked.connect(self.delete_selected_route)

        route_list_layout.addWidget(QLabel("Gespeicherte Routen:"))
        route_list_layout.addWidget(self.route_list_widget)
        route_list_layout.addWidget(self.delete_route_button)

        self.bottom_right_stack.addWidget(placeholder_widget)  # Index 0
        self.bottom_right_stack.addWidget(
            route_list_widget_container
        )  # Index 1

        return group_box

    # --- ADMIN-METHODEN (MIT KORREKTUR) ---

    def toggle_admin_mode(self, is_checked):
        """Schaltet die gesamte UI in den Admin-Modus um."""
        self.is_admin_mode = is_checked

        if self.is_admin_mode:
            if self.is_q1_maximized:
                self.toggle_q1_fullscreen()
            if self.is_sim_maximized:
                self.toggle_simulation_fullscreen()

            self.top_left_stack.setCurrentIndex(1)
            self.bottom_right_stack.setCurrentIndex(1)

            self.top_left_group_box.setTitle("Routen-Verwaltung")
            self.bottom_right_group_box.setTitle("Routen-Liste")
            self.bottom_left_group_box.setTitle("Routen-Editor")

            self.bottom_left_group_box.setEnabled(False)
            if self.item_q1:
                self.item_q1.setEnabled(False)

        else:
            self.cancel_drawing_mode()

            self.top_left_stack.setCurrentIndex(0)
            self.bottom_right_stack.setCurrentIndex(0)

            self.top_left_group_box.setTitle("Eingabeparameter")
            self.bottom_right_group_box.setTitle("Zukünftige Anforderungen")
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")

            self.bottom_left_group_box.setEnabled(True)
            if self.item_q1:
                self.item_q1.setEnabled(True)

    def start_drawing_mode(self):
        """Wird vom 'Neue Route'-Button ausgelöst."""
        self.is_drawing_mode = True

        # UI-Buttons anpassen
        self.new_route_button.setEnabled(False)
        self.route_list_widget.setEnabled(False)  # Liste sperren

        self.current_route_points.clear()
        self.clear_drawing_artifacts()

        pen = QPen(COLOR_ORANGE, 3)
        pen.setStyle(Qt.PenStyle.DashLine)

        self.current_route_path_item = QGraphicsPathItem()
        self.current_route_path_item.setPen(pen)
        self.sim_scene.addItem(self.current_route_path_item)

        # <<< KORREKTUR: ECHTER VOLLBILDMODUS >>>
        # Blende ALLE anderen Quadranten aus
        self.top_row_widget.hide()  # Blendet Oben-Links UND Oben-Rechts aus
        self.bottom_right_group_box.hide()

        # Zeige die Admin-Knöpfe (Speichern/Abbrechen)
        self.admin_button_container.show()

        self.bottom_left_group_box.setTitle("Routen-Editor (Zeichnen)")
        self.bottom_left_group_box.setEnabled(True)

    def cancel_drawing_mode(self):
        """Bricht das aktuelle Zeichnen ab."""
        if not self.is_drawing_mode:
            return

        self.is_drawing_mode = False

        # Buttons zurücksetzen
        self.new_route_button.setEnabled(True)
        self.route_list_widget.setEnabled(True)

        self.clear_drawing_artifacts()

        # <<< KORREKTUR: UI WIEDERHERSTELLEN >>>
        self.top_row_widget.show()  # Blendet Oben-Links/Rechts wieder ein
        self.bottom_right_group_box.show()

        # Verstecke die Admin-Knöpfe im Simulations-Quadrant
        self.admin_button_container.hide()

        self.bottom_left_group_box.setTitle("Routen-Editor")
        self.bottom_left_group_box.setEnabled(
            False
        )  # Zurück zum Admin-Standard

    def save_drawing_mode(self):
        """Speichert die gezeichnete Route."""
        if not self.is_drawing_mode or not self.current_route_points:
            self.cancel_drawing_mode()
            return

        # Hier können Sie QInputDialog nutzen, um einen Namen abzufragen
        route_name = f"Route_{len(self.all_routes) + 1}"

        self.all_routes[route_name] = list(self.current_route_points)

        self.route_list_widget.addItem(route_name)

        self.save_routes_to_json()

        # Beendet den Zeichenmodus und stellt die 4-Quadranten-Admin-UI wieder her
        self.cancel_drawing_mode()
        print(f"Route '{route_name}' gespeichert.")

    def add_waypoint(self, pos: QPointF):
        """Fügt einen Wegpunkt hinzu (wird von der Szene aufgerufen)."""
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
            self.current_route_path_item.setZValue(9)

    def clear_drawing_artifacts(self):
        """Entfernt temporäre Punkte und Linien aus der Szene."""
        if self.current_route_path_item:
            self.sim_scene.removeItem(self.current_route_path_item)
            self.current_route_path_item = None

        for item in self.current_route_point_items:
            self.sim_scene.removeItem(item)
        self.current_route_point_items.clear()

    def show_route_details(self, item: QListWidgetItem):
        """Zeigt eine Route an, wenn sie in der Liste angeklickt wird."""
        if self.is_drawing_mode:
            self.cancel_drawing_mode()

        self.clear_drawing_artifacts()

        route_name = item.text()
        if route_name not in self.all_routes:
            return

        points = self.all_routes[route_name]
        if not points:
            return

        pen = QPen(COLOR_TURQUOISE, 3)  # Andere Farbe für Vorschau
        path_item = QGraphicsPathItem()
        path_item.setPen(pen)
        path_item.setZValue(9)

        path = QPainterPath()
        path.moveTo(points[0])

        point_items = []
        for p in points:
            path.lineTo(p)
            dot = self.sim_scene.addEllipse(
                p.x() - 4,
                p.y() - 4,
                8,
                8,
                QPen(COLOR_DARK_TEXT),
                QBrush(COLOR_TURQUOISE),
            )
            dot.setZValue(10)
            point_items.append(dot)

        path_item.setPath(path)
        self.sim_scene.addItem(path_item)

        self.current_route_path_item = path_item
        self.current_route_point_items = point_items

    def delete_selected_route(self):
        """Löscht die ausgewählte Route."""
        selected_items = self.route_list_widget.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        route_name = item.text()

        if route_name in self.all_routes:
            del self.all_routes[route_name]

        self.route_list_widget.takeItem(self.route_list_widget.row(item))

        self.save_routes_to_json()

        self.clear_drawing_artifacts()
        print(f"Route '{route_name}' gelöscht.")

    # --- JSON-METHODEN ---

    def load_routes_from_json(self):
        """Lädt Routen aus der JSON-Datei beim Start."""
        try:
            if self.routes_file.exists():
                with open(self.routes_file, "r") as f:
                    routes_from_json = json.load(f)
                    self.all_routes.clear()
                    for name, points_list in routes_from_json.items():
                        self.all_routes[name] = [
                            QPointF(p[0], p[1]) for p in points_list
                        ]

                    print(
                        f"{len(self.all_routes)} Routen aus {self.routes_file} geladen."
                    )
                    self.populate_route_list_widget()
            else:
                print(
                    "Keine 'routes.json' gefunden. Starte mit leeren Routen."
                )
        except Exception as e:
            print(f"FEHLER beim Laden von 'routes.json': {e}")
            self.all_routes.clear()

    def save_routes_to_json(self):
        """Speichert alle aktuellen Routen in der JSON-Datei."""

        serializable_routes = {}
        for name, qpoints_list in self.all_routes.items():
            serializable_routes[name] = [[p.x(), p.y()] for p in qpoints_list]

        try:
            with open(self.routes_file, "w") as f:
                json.dump(serializable_routes, f, indent=4)
            print(f"Routen erfolgreich in {self.routes_file} gespeichert.")
        except Exception as e:
            print(f"FEHLER beim Speichern von 'routes.json': {e}")

    def populate_route_list_widget(self):
        """Aktualisiert die QListWidget mit den geladenen Routen."""
        self.route_list_widget.clear()
        for route_name in self.all_routes.keys():
            self.route_list_widget.addItem(route_name)

    # --- Zoom-Methoden (Unverändert) ---

    def toggle_q1_fullscreen(self):
        """Schaltet den Zoom für Q1 (Kassenbereich) um."""
        if not self.item_q1 or self.is_admin_mode:
            return

        self.is_q1_maximized = not self.is_q1_maximized

        if self.is_q1_maximized:
            if self.item_q2:
                self.item_q2.hide()
            if self.item_q3:
                self.item_q3.hide()
            if self.item_q4:
                self.item_q4.hide()
            self.minimize_q1_button.show()
            self.sim_view.fitInView(
                self.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )

            if self.is_sim_maximized:
                self.minimize_sim_button.hide()
                self.bottom_left_group_box.setTitle("Kassenbereich (Vollbild)")
            else:
                self.bottom_left_group_box.setTitle("Kassenbereich (Vollbild)")

        else:
            if self.item_q2:
                self.item_q2.show()
            if self.item_q3:
                self.item_q3.show()
            if self.item_q4:
                self.item_q4.show()
            self.minimize_q1_button.hide()
            self.sim_view.fitInView(
                self.sim_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
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

    def toggle_simulation_fullscreen(self):
        """Schaltet die Sichtbarkeit der Quadranten um (GESAMTE KARTE)."""
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
                self.item_q1.setEnabled(True)
        else:
            self.top_row_widget.show()
            self.bottom_right_group_box.show()
            self.minimize_sim_button.hide()
            self.bottom_left_group_box.setTitle("Live-Simulation (Miniatur)")
            if self.item_q1:
                self.item_q1.setEnabled(True)
            self.sim_view.fitInView(
                self.sim_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )


# --- Anwendung starten ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Globales Stylesheet "PROJEKT: PIEP" ---
    # WICHTIG: Das 'f' vor den Anführungszeichen ermöglicht die Variablen!
    app.setStyleSheet(
        f"""
        QWidget {{
            font-family: 'Segoe UI', 'Sans-Serif';
            font-size: 10pt;
            color: {COLOR_DARK_TEXT.name()};
        }}
        QMainWindow, QWidget {{
            background-color: {COLOR_WHITE_BG.name()};
        }}
        QGroupBox {{
            background-color: {COLOR_WHITE_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 5px;
            margin-top: 10px;
            padding: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
            left: 10px;
            color: {COLOR_TURQUOISE.name()};
            font-size: 11pt;
            font-weight: bold;
        }}
        
        QPushButton {{
            color: white; border: none; padding: 8px 14px;
            font-size: 10pt; font-weight: bold; border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BORDER.name()};
            color: {COLOR_MEDIUM_TEXT.name()};
        }}
        QPushButton#StartButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF8000, stop:1 {COLOR_ORANGE.name()});
        }}
        QPushButton#StartButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FF9000, stop:1 #FF7C00);
        }}
        
        QPushButton#MinimizeButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLOR_TURQUOISE.name()}, stop:1 #0090C0);
        }}
        QPushButton#MinimizeButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #00C0E0, stop:1 #00A0C0);
        }}
        
        QLineEdit, QSpinBox, QComboBox, QTextEdit, QListWidget {{
            background-color: {COLOR_LIGHT_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            padding: 5px;
            font-size: 10pt;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus, QListWidget:focus {{
            border: 1px solid {COLOR_ORANGE.name()};
        }}
        QListWidget::item:hover {{
            background-color: {COLOR_ORANGE.lighter(180).name()};
        }}
        QListWidget::item:selected {{
            background-color: {COLOR_ORANGE.name()};
            color: white;
        }}
        
        QComboBox::drop-down {{ border: none; }}
        QCheckBox::indicator {{
            width: 16px; height: 16px;
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            background-color: {COLOR_LIGHT_BG.name()};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLOR_ORANGE.name()};
            border-color: {COLOR_ORANGE.darker(120).name()};
        }}
        QSlider::groove:horizontal {{
            background: {COLOR_BORDER.name()}; height: 6px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {COLOR_ORANGE.name()};
            width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
        }}
        QGraphicsView {{
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
        }}
        QFormLayout QLabel {{
            font-size: 10pt;
            color: {COLOR_MEDIUM_TEXT.name()};
            padding-top: 5px;
        }}
        """
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
