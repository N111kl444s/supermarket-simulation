import sys
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
    QGraphicsPixmapItem,  # Standard Pixmap Item
    QGraphicsObject,  # Für klickbare Items mit Signalen
)

# QObject für Signale importieren
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QObject
from PyQt6.QtGui import (
    QPen,
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPixmap,
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
        # Wir rufen fitInView nicht mehr automatisch hier auf,
        # da die Zoom-Funktionen dies jetzt steuern.
        # Stattdessen manuell nach Bedarf aufrufen.
        if self.scene() and not self.sceneRect().isEmpty():
            # Wähle die korrekte Ansicht basierend auf dem Zustand
            # self.window() greift auf die MainWindow-Instanz zu
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
        self.setWindowTitle("Prototyp 4: Multi-Zoom-Layout (Projekt: Piep)")
        self.setGeometry(100, 100, 1400, 900)

        # Status für Karten-Vollbild
        self.is_sim_maximized = False
        # Status für Q1-Vollbild
        self.is_q1_maximized = False

        # Items initialisieren, um AttributeError zu verhindern
        self.item_q1 = None
        self.item_q2 = None
        self.item_q3 = None
        self.item_q4 = None

        self.scene_rect = QRectF()
        self.setup_ui()

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

        self.top_left_group = self.create_top_left_quadrant()
        self.top_right_group = self.create_top_right_quadrant()
        top_row_layout.addWidget(self.top_left_group, 1)
        top_row_layout.addWidget(self.top_right_group, 1)

        # --- Untere Reihe (als QWidget) ---
        self.bottom_row_widget = QWidget()
        bottom_row_layout = QHBoxLayout(self.bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(10)

        self.bottom_left_group = self.create_bottom_left_quadrant()
        self.bottom_right_group = self.create_bottom_right_quadrant()
        bottom_row_layout.addWidget(self.bottom_left_group, 1)
        bottom_row_layout.addWidget(self.bottom_right_group, 1)

        # Reihen zum Hauptlayout hinzufügen
        main_layout.addWidget(self.top_row_widget, 1)
        main_layout.addWidget(self.bottom_row_widget, 1)

    # --- Quadranten-Erstellungs-Methoden ---

    def create_top_left_quadrant(self):
        # (Unverändert)
        group_box = QGroupBox("Eingabeparameter")
        layout = QFormLayout(group_box)
        layout.setSpacing(10)
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
        layout.addRow(QLabel("Simulations-Name:"), self.sim_name_input)
        layout.addRow(QLabel("Aktor-Anzahl:"), self.actor_count_input)
        layout.addRow(QLabel("Geschwindigkeit:"), self.speed_slider)
        layout.addRow(QLabel("Simulations-Modus:"), self.sim_mode_combo)
        layout.addRow(self.logging_checkbox)
        layout.addRow(self.start_sim_button)
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
        """Erstellt die klickbare Simulations-Ansicht (Unten-Links)."""

        # GroupBox für den KARTEN-Zoom
        self.bottom_left_group = ClickableGroupBox(
            "Live-Simulation (Miniatur)"
        )
        self.bottom_left_group.clicked.connect(
            self.toggle_simulation_fullscreen
        )
        layout = QVBoxLayout(self.bottom_left_group)

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
        self.minimize_q1_button.setObjectName(
            "MinimizeButton"
        )  # Gleicher Stil

        # <<< KORREKTUR 1: Button-Verbindung >>>
        # Dieser Button muss den Q1-Zoom umschalten
        self.minimize_q1_button.clicked.connect(self.toggle_q1_fullscreen)
        self.minimize_q1_button.hide()
        layout.addWidget(self.minimize_q1_button)

        # --- Szene und View ---
        self.sim_scene = QGraphicsScene()
        self.sim_scene.setBackgroundBrush(QBrush(COLOR_LIGHT_BG))
        self.sim_view = AutoFitGraphicsView(self.sim_scene)

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

            # --- Items hinzufügen ---

            # Q1 (Klickbar für Q1-Zoom)
            self.item_q1 = ClickablePixmapItem(self.pix_q1)
            self.sim_scene.addItem(self.item_q1)
            self.item_q1.setPos(0, 0)
            self.item_q1.clicked.connect(
                self.toggle_q1_fullscreen
            )  # Signal verbinden

            # Q2 (Standard Item)
            self.item_q2 = self.sim_scene.addPixmap(self.pix_q2)
            self.item_q2.setPos(QUAD_WIDTH, 0)

            # Q3 (Standard Item)
            self.item_q3 = self.sim_scene.addPixmap(self.pix_q3)
            self.item_q3.setPos(0, QUAD_HEIGHT)

            # Q4 (Standard Item)
            self.item_q4 = self.sim_scene.addPixmap(self.pix_q4)
            self.item_q4.setPos(QUAD_WIDTH, QUAD_HEIGHT)

            # Szene-Rechteck auf Gesamtgröße (1600x900) setzen
            total_width = QUAD_WIDTH * 2
            total_height = QUAD_HEIGHT * 2
            self.scene_rect = QRectF(0, 0, total_width, total_height)
            self.sim_scene.setSceneRect(self.scene_rect)

            # Ansicht initial anpassen
            self.sim_view.fitInView(
                self.scene_rect, Qt.AspectRatioMode.KeepAspectRatio
            )

        except Exception as e:
            print(f"FEHLER beim Laden der Quadranten-Bilder: {e}")
            text_item = self.sim_scene.addText(
                f"Fehler: 4 Quadranten-Bilder (z.B. quadrant_1.png) in {IMAGE_DIR} nicht gefunden.\n\nERROR: {e}"
            )
            text_item.setDefaultTextColor(QColor("red"))
            self.sim_scene.setSceneRect(0, 0, 400, 300)

        layout.addWidget(self.sim_view)
        return self.bottom_left_group

    def create_bottom_right_quadrant(self):
        # (Unverändert)
        group_box = QGroupBox("Zukünftige Anforderungen")
        layout = QVBoxLayout(group_box)
        placeholder_text = "Hier ist Platz für zukünftige Anforderungen..."
        self.placeholder_widget = QTextEdit()
        self.placeholder_widget.setReadOnly(True)
        self.placeholder_widget.setText(placeholder_text)
        layout.addWidget(self.placeholder_widget)
        return group_box

    # --- Zoom-Methoden (ANGEPASSTE LOGIK) ---

    def toggle_q1_fullscreen(self):
        """
        Schaltet den Zoom für Q1 (Kassenbereich) um.
        Kann aus der Miniaturansicht ODER der Karten-Vollansicht aufgerufen werden.
        """

        # Safety-Check, falls Bilder nicht geladen wurden
        if not self.item_q1:
            return

        self.is_q1_maximized = not self.is_q1_maximized

        if self.is_q1_maximized:
            # --- Q1 MAXIMIEREN ---
            if self.item_q2:
                self.item_q2.hide()
            if self.item_q3:
                self.item_q3.hide()
            if self.item_q4:
                self.item_q4.hide()

            # Q1-Minimieren-Button anzeigen
            self.minimize_q1_button.show()

            # Ansicht auf Q1 zoomen
            self.sim_view.fitInView(
                self.item_q1.boundingRect(), Qt.AspectRatioMode.KeepAspectRatio
            )

            if self.is_sim_maximized:
                # Fall A: Waren im KARTEN-Vollbild
                self.minimize_sim_button.hide()  # Karten-Button ausblenden
                self.bottom_left_group.setTitle("Kassenbereich (Vollbild)")
            else:
                # Fall B: Waren in der MINIATUR-Ansicht
                self.bottom_left_group.setTitle("Kassenbereich (Vollbild)")
                # <<< KORREKTUR 2: Diese Zeile entfernt >>>
                # self.bottom_left_group.setEnabled(False) # Deaktiviert Klick auf GroupBox

        else:
            # --- Q1 MINIMIEREN (Zurück zum vorherigen Zustand) ---
            if self.item_q2:
                self.item_q2.show()
            if self.item_q3:
                self.item_q3.show()
            if self.item_q4:
                self.item_q4.show()

            self.minimize_q1_button.hide()

            # Ansicht auf ganze Szene zurücksetzen
            self.sim_view.fitInView(
                self.sim_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )

            if self.is_sim_maximized:
                # Fall A: Zurück zum KARTEN-Vollbild
                self.minimize_sim_button.show()  # Karten-Button wieder anzeigen
                self.bottom_left_group.setTitle("Live-Simulation (Vollbild)")
            else:
                # Fall B: Zurück zur MINIATUR-Ansicht
                self.bottom_left_group.setTitle("Live-Simulation (Miniatur)")
                # <<< KORREKTUR 2: Diese Zeile entfernt >>>
                # self.bottom_left_group.setEnabled(True) # Klick auf GroupBox aktivieren

    def toggle_simulation_fullscreen(self):
        """
        Schaltet die Sichtbarkeit der Quadranten um (GESAMTE KARTE).
        Wird von der GroupBox oder dem Karten-Minimieren-Button ausgelöst.
        """

        # Wenn Q1 maximiert ist, soll ein Klick auf die GroupBox
        # (die jetzt nicht mehr deaktiviert ist)
        # AUCH als "Zurück" von Q1 fungieren.
        if self.is_q1_maximized:
            self.toggle_q1_fullscreen()
            return

        self.is_sim_maximized = not self.is_sim_maximized

        if self.is_sim_maximized:
            # --- KARTE MAXIMIEREN ---
            self.top_row_widget.hide()
            self.bottom_right_group.hide()

            self.minimize_sim_button.show()
            self.bottom_left_group.setTitle("Live-Simulation (Vollbild)")

            if self.item_q1:
                self.item_q1.setEnabled(True)

        else:
            # --- KARTE MINIMIEREN ---
            self.top_row_widget.show()
            self.bottom_right_group.show()

            self.minimize_sim_button.hide()

            self.bottom_left_group.setTitle("Live-Simulation (Miniatur)")

            if self.item_q1:
                self.item_q1.setEnabled(True)

            self.sim_view.fitInView(
                self.sim_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )


# --- Anwendung starten ---
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- Globales Stylesheet "PROJEKT: PIEP" ---
    app.setStyleSheet(
        """
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
        
        QLineEdit, QSpinBox, QComboBox, QTextEdit {{
            background-color: {COLOR_LIGHT_BG.name()};
            border: 1px solid {COLOR_BORDER.name()};
            border-radius: 4px;
            padding: 5px;
            font-size: 10pt;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
            border: 1px solid {COLOR_ORANGE.name()};
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
