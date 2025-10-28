import sys
import time
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QSplitter,
    QHeaderView,
    QGraphicsEllipseItem,
    QToolTip,
    QSlider,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QLineF, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter

import pyqtgraph as pg

# Konstanten für die Simulation
ACTOR_NAME = "SimBot-01"
DEFAULT_ACTOR_SPEED_PPS = 150.0
SIM_UPDATE_MS = 16
WAYPOINT_SIZE = 10
ACTOR_SIZE = 12

# <<< NEUE FARBPALETTE BASIEREND AUF DEM LOGO >>>
COLOR_ORANGE = QColor("#FF6A00")  # Hauptakzent: Kräftiges Orange
COLOR_TURQUOISE = QColor("#00B0D0")  # Sekundär: Helles Türkis/Blau
COLOR_GREEN = QColor("#50C878")  # Tertiär: Mittleres Grün
COLOR_DARK_TEXT = QColor("#333333")  # Dunkelgrau für Haupttext
COLOR_MEDIUM_TEXT = QColor("#666666")  # Mittelgrau
COLOR_LIGHT_BG = QColor("#F8F8F8")  # Sehr helles Grau für UI-Elemente
COLOR_WHITE_BG = QColor("#FFFFFF")  # Reinweiß
COLOR_BORDER = QColor("#E0E0E0")  # Heller Rand


# 1. Benutzerdefinierte Szene
class SimGraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Hintergrund wird in setup_ui gesetzt

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.parent().is_running:
                item = self.itemAt(
                    event.scenePos(), self.parent().view.transform()
                )
                if item is None:
                    self.parent().add_waypoint(event.scenePos())
        super().mousePressEvent(event)


# 2. Actor-Item (Projekt: Piep Stil - Orange)
class ActorItem(QGraphicsEllipseItem):
    def __init__(self, x, y, size, parent_window):
        super().__init__(-size / 2, -size / 2, size, size)

        # Akzentfarbe Orange aus der neuen Palette
        self.setBrush(QBrush(COLOR_ORANGE))
        self.setPen(QPen(COLOR_ORANGE.darker(150)))  # Etwas dunklerer Rand

        self.setAcceptHoverEvents(True)
        self.setPos(QPointF(x, y))
        self.parent_window = parent_window
        self.speed = 0.0
        self.update_tooltip()

    def update_tooltip(self):
        self.tooltip_text = (
            f"Typ: Aktor\nName: {ACTOR_NAME}\nSpeed: {self.speed:.2f} px/s"
        )
        self.setToolTip(self.tooltip_text.replace("\n", " | "))

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.toolTip())
        event.accept()

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_window.show_info(self.tooltip_text)
            event.accept()
        super().mousePressEvent(event)


# 3. WaypointItem (Projekt: Piep Stil - Türkis)
class WaypointItem(QGraphicsEllipseItem):
    def __init__(self, x, y, size, wp_id, parent_window):
        super().__init__(-size / 2, -size / 2, size, size)
        self.setPos(QPointF(x, y))

        # Sekundäre Akzentfarbe Türkis aus der neuen Palette
        self.setBrush(
            QBrush(COLOR_TURQUOISE.lighter(130))
        )  # Etwas heller für bessere Sichtbarkeit
        self.setPen(QPen(COLOR_TURQUOISE.darker(150)))

        self.setAcceptHoverEvents(True)
        self.setZValue(1)
        self.wp_id = wp_id
        self.parent_window = parent_window

        self.info_text = (
            f"Typ: Wegpunkt\nID: {self.wp_id}\nPos: ({x:.1f}, {y:.1f})"
        )
        self.setToolTip(self.info_text.replace("\n", " | "))

    def hoverEnterEvent(self, event):
        QToolTip.showText(event.screenPos(), self.toolTip())
        event.accept()

    def hoverLeaveEvent(self, event):
        QToolTip.hideText()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_window.show_info(self.info_text)
            event.accept()
        super().mousePressEvent(event)


# 4. Das Hauptfenster
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulations-Prototyp (Projekt: Piep)")
        self.setGeometry(100, 100, 1200, 800)

        # Simulations-Status
        self.waypoints = []
        self.actor = None
        self.is_running = False
        self.start_time = 0.0
        self.current_target_index = 0
        self.actor_speed = DEFAULT_ACTOR_SPEED_PPS
        self.total_elapsed_at_pause = 0.0

        # Plot-Daten
        self.plot_times = []
        self.plot_indices = []

        # UI-Elemente initialisieren
        self.setup_ui()

        # Timer
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_simulation)
        self.stopwatch_timer = QTimer(self)
        self.stopwatch_timer.timeout.connect(self.update_stopwatch)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)

        # --- Steuerungsknöpfe ---
        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("StartButton")
        self.start_button.clicked.connect(self.on_start)

        self.stop_button = QPushButton("Stopp")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.clicked.connect(self.on_stop)
        self.stop_button.setEnabled(False)

        self.reset_button = QPushButton("Alles zurücksetzen")
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.clicked.connect(self.on_clear_all)

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.stop_button)
        left_layout.addLayout(controls_layout)
        left_layout.addWidget(self.reset_button)

        # --- Geschwindigkeitsregler ---
        speed_label_title = QLabel("Geschwindigkeit:")
        speed_label_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        speed_slider_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 500)
        self.speed_slider.setValue(int(self.actor_speed))
        self.speed_slider.valueChanged.connect(self.on_speed_changed)

        self.speed_label = QLabel(f"{self.actor_speed:.0f} px/s")
        self.speed_label.setMinimumWidth(60)

        speed_slider_layout.addWidget(self.speed_slider)
        speed_slider_layout.addWidget(self.speed_label)

        left_layout.addWidget(speed_label_title)
        left_layout.addLayout(speed_slider_layout)

        # --- Stoppuhr ---
        stopwatch_label_title = QLabel("Simulationszeit:")
        stopwatch_label_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.stopwatch_label = QLabel("0.00 s")
        self.stopwatch_label.setObjectName("StopwatchLabel")
        self.stopwatch_label.setFont(QFont("Consolas", 14))
        self.stopwatch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_layout.addWidget(stopwatch_label_title)
        left_layout.addWidget(self.stopwatch_label)

        # --- Tabelle (Wegpunkt-Log) ---
        table_label = QLabel("Wegpunkt-Log:")
        table_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(
            ["Wegpunkt ID", "Erreicht nach (s)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)

        left_layout.addWidget(table_label)
        left_layout.addWidget(self.table, 2)

        # --- Info-Feld ---
        info_label = QLabel("Objekt-Information:")
        info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        self.info_box = QTextEdit()
        self.info_box.setObjectName("InfoBox")
        self.info_box.setReadOnly(True)
        self.info_box.setFont(QFont("Consolas", 10))

        left_layout.addWidget(info_label)
        left_layout.addWidget(self.info_box, 1)

        splitter.addWidget(left_panel)

        # ----- Rechte Seite (Visualisierung) -----
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        vis_splitter = QSplitter(Qt.Orientation.Vertical)

        self.scene = SimGraphicsScene(self)
        self.scene.setBackgroundBrush(
            QBrush(COLOR_LIGHT_BG)
        )  # Hellgrauer Hintergrund
        self.scene.setSceneRect(0, 0, 700, 500)

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        vis_splitter.addWidget(self.view)

        # Diagramm (PyQtGraph)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(COLOR_WHITE_BG)  # Weißer Hintergrund
        self.plot_widget.setTitle(
            "Zeit pro Wegpunkt",
            color=COLOR_DARK_TEXT.name(),  # Dunkelgrau
            size="12pt",
        )
        self.plot_widget.setLabel(
            "left", "Zeit (s)", color=COLOR_MEDIUM_TEXT.name()
        )
        self.plot_widget.setLabel(
            "bottom", "Wegpunkt ID", color=COLOR_MEDIUM_TEXT.name()
        )
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Plot-Farbe: Passend zur Logofarbe Grün
        plot_pen_color = COLOR_GREEN.name()
        self.plot_data_item = self.plot_widget.plot(
            pen=pg.mkPen(color=plot_pen_color, width=2),
            symbol="o",
            symbolBrush=plot_pen_color,
            symbolSize=8,
        )
        vis_splitter.addWidget(self.plot_widget)

        vis_splitter.setSizes(
            [int(self.height() * 0.6), int(self.height() * 0.4)]
        )
        right_layout.addWidget(vis_splitter)
        splitter.addWidget(right_panel)
        splitter.setSizes([int(self.width() * 0.35), int(self.width() * 0.65)])

    def show_info(self, text):
        """Zeigt den übergebenen Text im Info-Feld an."""
        self.info_box.setText(text)

    # --- Kernfunktionen & Slots ---

    def add_waypoint(self, pos):
        """Fügt einen neuen klickbaren Wegpunkt hinzu."""
        wp_id = len(self.waypoints)

        wp_item = WaypointItem(pos.x(), pos.y(), WAYPOINT_SIZE, wp_id, self)
        self.scene.addItem(wp_item)

        text = self.scene.addText(f"WP {wp_id}", QFont("Arial", 8))
        text.setPos(pos.x() + WAYPOINT_SIZE / 2, pos.y() - WAYPOINT_SIZE / 2)
        text.setZValue(0)

        self.waypoints.append(pos)
        print(
            f"Wegpunkt {wp_id} hinzugefügt bei: ({pos.x():.1f}, {pos.y():.1f})"
        )

    def on_speed_changed(self, value):
        """Aktualisiert die Geschwindigkeit, wenn der Slider bewegt wird."""
        self.actor_speed = float(value)
        self.speed_label.setText(f"{self.actor_speed:.0f} px/s")
        if self.actor:
            self.actor.speed = self.actor_speed
            self.actor.update_tooltip()

    def on_start(self):
        """Startet die Simulation."""
        if self.is_running or len(self.waypoints) < 2:
            print(
                "Nicht genügend Wegpunkte (min 2) oder Simulation läuft bereits."
            )
            return

        print(
            f"Simulation gestartet. Geschwindigkeit: {self.actor_speed} px/s"
        )
        self.is_running = True

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.reset_button.setEnabled(False)

        if not self.actor:
            start_pos = self.waypoints[0]
            self.actor = ActorItem(
                start_pos.x(), start_pos.y(), ACTOR_SIZE, self
            )
            self.scene.addItem(self.actor)
            self.log_waypoint(0, 0.0)
            self.current_target_index = 1

        self.actor_speed = self.speed_slider.value()
        self.actor.speed = self.actor_speed
        self.actor.update_tooltip()

        self.start_time = time.time()
        self.sim_timer.start(SIM_UPDATE_MS)
        self.stopwatch_timer.start(50)

    def on_stop(self):
        """Stoppt die Simulation, behält aber den Fortschritt bei."""
        if not self.is_running:
            return
        print("Simulation angehalten.")
        self.is_running = False
        self.sim_timer.stop()
        self.stopwatch_timer.stop()
        self.total_elapsed_at_pause += time.time() - self.start_time
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.speed_slider.setEnabled(True)
        if self.actor:
            self.actor.speed = 0.0
            self.actor.update_tooltip()

    def on_clear_all(self):
        """Setzt die gesamte Simulation zurück."""
        print("Simulation wird komplett zurückgesetzt.")
        if self.is_running:
            self.on_stop()

        self.waypoints = []
        self.current_target_index = 0
        self.start_time = 0.0
        self.total_elapsed_at_pause = 0.0

        self.stopwatch_label.setText("0.00 s")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.speed_slider.setEnabled(True)
        self.speed_slider.setValue(int(DEFAULT_ACTOR_SPEED_PPS))
        self.info_box.clear()

        self.scene.clear()
        self.actor = None
        self.table.setRowCount(0)
        self.plot_times = []
        self.plot_indices = []
        self.plot_data_item.setData(self.plot_indices, self.plot_times)

    def update_stopwatch(self):
        """Aktualisiert die Stoppuhr-Anzeige."""
        if not self.is_running:
            return
        elapsed = (time.time() - self.start_time) + self.total_elapsed_at_pause
        self.stopwatch_label.setText(f"{elapsed:.2f} s")

    def update_simulation(self):
        """Der Haupt-Update-Loop (Logik für zentrierte Items)."""
        if not self.is_running or self.actor is None:
            return
        if self.current_target_index >= len(self.waypoints):
            self.finish_simulation()
            return

        current_center = self.actor.pos()
        target_pos = self.waypoints[self.current_target_index]

        dx = target_pos.x() - current_center.x()
        dy = target_pos.y() - current_center.y()
        distance = (dx * dx + dy * dy) ** 0.5

        time_delta_s = SIM_UPDATE_MS / 1000.0
        step_distance = self.actor_speed * time_delta_s

        if distance <= step_distance or distance == 0.0:
            self.actor.setPos(target_pos)
            elapsed_time = (
                time.time() - self.start_time
            ) + self.total_elapsed_at_pause
            self.log_waypoint(self.current_target_index, elapsed_time)
            self.current_target_index += 1
            return

        ux = dx / distance
        uy = dy / distance
        move_x = ux * step_distance
        move_y = uy * step_distance
        new_center = QPointF(
            current_center.x() + move_x, current_center.y() + move_y
        )
        self.actor.setPos(new_center)

    def finish_simulation(self):
        """Wird aufgerufen, wenn der letzte Wegpunkt erreicht ist."""
        print("Simulation beendet (letzter Wegpunkt erreicht).")
        self.on_stop()

    def log_waypoint(self, index, elapsed_time):
        """Fügt einen Eintrag zur Tabelle und zum Diagramm hinzu."""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.table.setItem(row_count, 0, QTableWidgetItem(f"{index}"))
        self.table.setItem(
            row_count, 1, QTableWidgetItem(f"{elapsed_time:.3f}")
        )
        self.plot_indices.append(index)
        self.plot_times.append(elapsed_time)
        self.plot_data_item.setData(self.plot_indices, self.plot_times)


# --- Anwendung starten ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Globales Stylesheet "PROJEKT: PIEP" ---
    # BASIEREND AUF DEM BEREITGESTELLTEN LOGO
    app.setStyleSheet(
        """
        /* Globaler Stil: Weißer Hintergrund, Sans-Serif Schrift */
        QWidget {{
            font-family: 'Segoe UI', 'Sans-Serif';
            font-size: 10pt;
            color: {COLOR_DARK_TEXT.name()};
        }}
        
        QMainWindow, QWidget {{
            background-color: {COLOR_WHITE_BG.name()};
        }}

        QLabel[font-weight="bold"] {{
            color: {COLOR_TURQUOISE.name()}; /* Türkis für Titel */
            font-size: 12pt;
        }}

        QPushButton {{
            color: white;
            border: none;
            padding: 8px 14px;
            font-size: 10pt;
            font-weight: bold;
            border-radius: 4px;
        }}
        QPushButton:disabled {{
            background-color: {COLOR_BORDER.name()};
            color: {COLOR_MEDIUM_TEXT.name()};
        }}

        /* Start-Button: Hauptakzentfarbe Orange */
        QPushButton#StartButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #FF8000, stop:1 {COLOR_ORANGE.name()});
        }}
        QPushButton#StartButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #FF9000, stop:1 #FF7C00);
        }}

        /* Stop/Reset-Buttons: Türkis */
        QPushButton#StopButton, QPushButton#ResetButton {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 {COLOR_TURQUOISE.name()}, stop:1 #0090C0);
        }}
        QPushButton#StopButton:hover, QPushButton#ResetButton:hover {{
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #00C0E0, stop:1 #00A0C0);
        }}

        /* Stoppuhr: Hintergrund hellgrau, Text Türkis */
        QLabel#StopwatchLabel {{
            background-color: {COLOR_LIGHT_BG.name()};
            color: {COLOR_TURQUOISE.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            padding: 5px;
            font-family: 'Consolas', 'Courier New', 'monospace';
            font-size: 14pt;
        }}

        /* Info-Box: Hintergrund hellgrau, Text dunkelgrau */
        QTextEdit#InfoBox {{
            background-color: {COLOR_LIGHT_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            font-family: 'Consolas', 'Courier New', 'monospace';
            font-size: 10pt;
        }}

        /* Tabelle: Klare Linien, Header Türkis */
        QTableWidget {{
            border: 1px solid {COLOR_BORDER.name()};
            gridline-color: {COLOR_BORDER.name()};
        }}
        QHeaderView::section {{
            background-color: {COLOR_LIGHT_BG.name()};
            color: {COLOR_TURQUOISE.name()};
            padding: 4px;
            border: none;
            border-bottom: 1px solid {COLOR_BORDER.name()};
            font-weight: bold;
        }}

        /* Slider: Hauptakzent Orange */
        QSlider::groove:horizontal {{
            background: {COLOR_BORDER.name()};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {COLOR_ORANGE.name()};
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        
        QSplitter::handle {{
            background-color: {COLOR_BORDER.name()};
        }}
        QSplitter::handle:hover {{
            background-color: {COLOR_BORDER.darker(110).name()};
        }}
        
        QGraphicsView {{
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
        }}
        """
    )

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
